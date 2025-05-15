import unittest
import json
import time
from unittest.mock import patch
from ds_protocol import (
    format_auth_message,
    format_direct_message,
    format_fetch_request,
    extract_json,
    is_valid_response,
    DSPProtocolError,
    ServerResponse
)



class TestDSPProtocol(unittest.TestCase):
    """Test cases for the DSP protocol implementation."""

    def test_format_auth_message(self):
        """Test formatting authentication message."""
        result = format_auth_message("testuser", "testpass")
        expected = ('{"authenticate": {\n    "username": "testuser",\n    "password": "testpass"\n}}')
        self.assertEqual(json.loads(result), json.loads(expected))

    def test_format_direct_message(self):
        """Test formatting direct message."""
        with patch('time.time', return_value=1234567890.0):
            result = format_direct_message(
                "test-token", "recipient", "Hello"
            )
            expected = ('{\n    "token": "test-token",\n    "directmessage": {\n        "message": "Hello",\n        "recipient": "recipient",\n        "timestamp": 1234567890.0\n    }\n}')
            self.assertEqual(json.loads(result), json.loads(expected))

    def test_format_fetch_request(self):
        """Test formatting fetch request"""
        result = format_fetch_request("test-token", "all")
        expected = '{"token": "test-token", "fetch": "all"}'
        self.assertEqual(json.loads(result), json.loads(expected))
        
        result = format_fetch_request("test-token", "unread")
        expected = '{"token": "test-token", "fetch": "unread"}'
        self.assertEqual(json.loads(result), json.loads(expected))
        
        with self.assertRaises(DSPProtocolError):
            format_fetch_request("test-token", "invalid")

    def test_extract_json_valid(self):
        """Test extracting valid JSON response."""
        response = ('{"response": {\n    "type": "ok",\n    "message": "Success",\n    "token": "test-token"\n}}')
        result = extract_json(response)
        self.assertEqual(result.type, "ok")
        self.assertEqual(result.message, "Success")
        self.assertEqual(result.token, "test-token")
        self.assertEqual(result.messages, [])

        # Test with messages
        response = ('{"response": {\n    "type": "ok",\n    "messages": [{"message": "Hi"}]\n}}')
        result = extract_json(response)
        self.assertEqual(result.type, "ok")
        self.assertEqual(result.messages, [{"message": "Hi"}])

    def test_extract_json_invalid(self):
        """Test extracting invalid JSON response"""
        with self.assertRaises(DSPProtocolError):
            extract_json('invalid json')
            
        with self.assertRaises(DSPProtocolError):
            extract_json('{"not_response": {}}')

    def test_is_valid_response(self):
        """Test response validation."""
        valid_response = ServerResponse(
            type="ok", message="Success", token="test", messages=[]
        )
        self.assertTrue(is_valid_response(valid_response))

        invalid_response = ServerResponse(
            type="error", message="Failed", token=None, messages=[]
        )
        self.assertFalse(is_valid_response(invalid_response))
        self.assertFalse(is_valid_response(None))


if __name__ == '__main__':
    unittest.main()
