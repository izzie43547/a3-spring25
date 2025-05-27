"""
Test cases for DSP protocol implementation.

This module contains unit tests for the DSP protocol functions.
"""

import unittest
import json
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
    """Test cases for DSP protocol implementation."""

    def test_format_auth_message(self):
        """Test formatting authentication message.

        Verifies that format_auth_message correctly formats the authentication
        message with the provided username and password.
        """
        result = format_auth_message("testuser", "testpass")
        expected = {
            "authenticate": {
                "username": "testuser",
                "password": "testpass"
            }
        }
        self.assertEqual(json.loads(result), expected)

    def test_format_direct_message(self):
        """Test formatting direct message."""
        msg = format_direct_message("recipient", "Hello", "test-token")
        expected = '{"directmessage": {"entry": "Hello", "recipient": "recipient", "token": "test-token"}}'
        self.assertEqual(msg, expected)

        # Verify message structure
        dm_msg = json.loads(msg)
        self.assertIn("directmessage", dm_msg)
        self.assertIn("entry", dm_msg["directmessage"])
        self.assertIn("recipient", dm_msg["directmessage"])
        self.assertIn("token", dm_msg["directmessage"])

        # Test with empty message
        empty_msg = format_direct_message("recipient", "", "test-token")
        empty_dm = json.loads(empty_msg)
        self.assertEqual(empty_dm["directmessage"]["entry"], "")

    def test_format_fetch_request(self):
        """Test formatting fetch request."""
        msg = format_fetch_request("test-token")
        expected = '{"directmessage": {"token": "test-token"}}'
        self.assertEqual(msg, expected)

        # Verify request structure
        fetch_msg = json.loads(msg)
        self.assertIn("directmessage", fetch_msg)
        self.assertIn("token", fetch_msg["directmessage"])

        # Test invalid fetch type
        with self.assertRaises(DSPProtocolError):
            format_fetch_request("test-token", "invalid")

        # Test valid fetch types
        for fetch_type in ["all", "unread"]:
            msg = format_fetch_request("test-token", fetch_type)
            fetch_msg = json.loads(msg)
            self.assertEqual(fetch_msg["directmessage"]["fetch"], fetch_type)

        # Test with empty token
        with self.assertRaises(ValueError):
            format_fetch_request("")

    def test_extract_json_valid(self):
        """Test extracting valid JSON response."""
        response = '{"response": {"type": "ok", "message": "Success", "token": "test-token"}}'
        result = extract_json(response)
        self.assertEqual(result.type, "ok")
        self.assertEqual(result.message, "Success")
        self.assertEqual(result.token, "test-token")
        self.assertEqual(result.messages, [])

        # Test with messages
        response = '{"response": {"type": "ok", "messages": [{"message": "Hi"}]}}'
        result = extract_json(response)
        self.assertEqual(result.type, "ok")
        self.assertEqual(result.messages, [{"message": "Hi"}])

        # Test with multiple messages
        response = '{"response": {"type": "ok", "messages": [{"message": "Hi"}, {"message": "Hello"}]}}'
        result = extract_json(response)
        self.assertEqual(result.type, "ok")
        self.assertEqual(len(result.messages), 2)
        self.assertEqual(result.messages[0]["message"], "Hi")
        self.assertEqual(result.messages[1]["message"], "Hello")

        # Test with malformed JSON
        with self.assertRaises(DSPProtocolError):
            extract_json('{"response": {"type": "ok", "messages": ["not_an_object"]}}')

        # Test with invalid message format
        with self.assertRaises(DSPProtocolError):
            extract_json('{"response": {"type": "ok", "messages": [{"invalid": "field"}]}}')

        # Test with malformed JSON
        with self.assertRaises(DSPProtocolError):
            extract_json('{"response": {"type": "ok", "messages": ["not_an_object"]}}')

        # Test with invalid message format
        with self.assertRaises(DSPProtocolError):
            extract_json('{"response": {"type": "ok", "messages": [{"invalid": "field"}]}}')

        # Test with empty messages
        response = '{"response": {"type": "ok", "messages": []}}'
        result = extract_json(response)
        self.assertEqual(result.type, "ok")
        self.assertEqual(result.messages, [])

        # Verify JSON structure
        self.assertTrue(hasattr(result, 'type'))
        self.assertTrue(hasattr(result, 'message'))
        self.assertTrue(hasattr(result, 'token'))

        # Test with messages
        response = '{"response": {"type": "ok", "messages": [{"message": "Hi"}]}}'
        result = extract_json(response)
        self.assertEqual(result.type, "ok")
        self.assertEqual(result.messages, [{"message": "Hi"}])

    def test_extract_json_invalid(self):
        """Test extracting invalid JSON response."""
        with self.assertRaises(DSPProtocolError):
            extract_json("invalid json")

        with self.assertRaises(DSPProtocolError):
            extract_json("{\"response\": {}}")

    def test_is_valid_response(self):
        """Test validating response type."""
        self.assertTrue(is_valid_response({"type": "ok"}))
        self.assertTrue(is_valid_response({"type": "error"}))
        self.assertFalse(is_valid_response({"type": "invalid"}))
        self.assertFalse(is_valid_response({}))

    def test_server_response(self):
        """Test ServerResponse namedtuple."""
        response = ServerResponse("ok", "Success", "test-token", [])
        self.assertEqual(response.type, "ok")
        self.assertEqual(response.message, "Success")
        self.assertEqual(response.token, "test-token")
        self.assertEqual(response.messages, [])

        # Verify response structure
        self.assertTrue(hasattr(response, 'type'))
        self.assertTrue(hasattr(response, 'message'))
        self.assertTrue(hasattr(response, 'token'))
        self.assertTrue(hasattr(response, 'messages'))

if __name__ == '__main__':
    unittest.main()
