import unittest
import socket
import json
import time
from unittest.mock import Mock, patch
from ds_messenger import DirectMessage, DirectMessenger

class TestDirectMessage(unittest.TestCase):
    def test_direct_message_creation(self):
        """Test DirectMessage initialization and properties"""
        dm = DirectMessage(
            recipient="recipient",
            sender="sender",
            message="Hello",
            timestamp=1234567890.0
        )
        self.assertEqual(dm.recipient, "recipient")
        self.assertEqual(dm.sender, "sender")
        self.assertEqual(dm.message, "Hello")
        self.assertEqual(dm.timestamp, 1234567890.0)

class TestDirectMessenger(unittest.TestCase):
    def setUp(self):
        self.messenger = DirectMessenger(
            dsuserver="localhost",
            username="testuser",
            password="testpass",
            is_test=True  # Enable test mode to avoid actual connections
        )
        
    @patch('socket.socket')
    def test_send_message_success(self, mock_socket):
        """Test successful message sending"""
        # Mock the socket and its methods
        mock_sock_instance = Mock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.makefile.return_value.readline.return_value = json.dumps({
            "response": {"type": "ok", "message": "Message sent"}
        })
        
        # Initialize and send message
        self.messenger._connect = Mock()
        self.messenger._authenticate = Mock(return_value=True)
        self.messenger.token = "test-token"
        
        # Set up the mock response for _receive
        self.messenger._receive = Mock(return_value=json.dumps({
            "response": {"type": "ok", "message": "Message sent"}
        }))
        
        result = self.messenger.send("Hello", "recipient")
        self.assertTrue(result)
        
    @patch('socket.socket')
    def test_retrieve_new_messages(self, mock_socket):
        """Test retrieving new messages"""
        # Mock server response
        test_messages = [{
            "message": "Hello",
            "from": "user1",
            "timestamp": time.time()
        }]
        
        # Set up the mock response for _receive
        self.messenger._receive = Mock(return_value=json.dumps({
            "response": {
                "type": "ok",
                "messages": test_messages
            }
        }))
        
        # Initialize and retrieve messages
        self.messenger._connect = Mock()
        self.messenger._authenticate = Mock(return_value=True)
        self.messenger.token = "test-token"
        
        messages = self.messenger.retrieve_new()
        self.assertEqual(len(messages), 1)
        self.assertIsInstance(messages[0], DirectMessage)
        self.assertEqual(messages[0].message, "Hello")
        self.assertEqual(messages[0].sender, "user1")

    @patch('socket.socket')
    def test_retrieve_all_messages(self, mock_socket):
        """Test retrieving all messages"""
        # Mock server response
        test_messages = [
            {"message": "Hello", "from": "user1", "timestamp": time.time()},
            {"message": "Hi", "recipient": "user2", "timestamp": time.time()}
        ]
        
        # Set up the mock response for _receive
        self.messenger._receive = Mock(return_value=json.dumps({
            "response": {
                "type": "ok",
                "messages": test_messages
            }
        }))
        
        # Initialize and retrieve messages
        self.messenger._connect = Mock()
        self.messenger._authenticate = Mock(return_value=True)
        self.messenger.token = "test-token"
        
        messages = self.messenger.retrieve_all()
        self.assertEqual(len(messages), 2)
        self.assertIsInstance(messages[0], DirectMessage)
        self.assertIsInstance(messages[1], DirectMessage)

    def test_parse_messages(self):
        """Test message parsing"""
        test_messages = [
            {"message": "Hello", "from": "user1", "timestamp": 1234567890.0},
            {"message": "Hi", "recipient": "user2", "timestamp": 1234567891.0}
        ]
        
        # Set username for testing
        self.messenger.username = "user2"
        
        # Parse messages
        parsed = self.messenger._parse_messages(test_messages)
        
        # Verify results
        self.assertEqual(len(parsed), 2)
        
        # First message (incoming)
        self.assertEqual(parsed[0].message, "Hello")
        self.assertEqual(parsed[0].sender, "user1")
        self.assertEqual(parsed[0].recipient, "user2")
        
        # Second message (outgoing)
        self.assertEqual(parsed[1].message, "Hi")
        self.assertEqual(parsed[1].sender, "user2")
        self.assertEqual(parsed[1].recipient, "user2")

if __name__ == '__main__':
    unittest.main()
