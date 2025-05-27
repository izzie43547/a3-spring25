import unittest
import socket
import json
import time
from unittest.mock import Mock, patch
from ds_messenger import DirectMessenger, DirectMessage


class TestDirectMessengerCoverage(unittest.TestCase):
    """Test cases to improve coverage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.messenger = DirectMessenger(
            dsuserver="localhost",
            username="testuser",
            password="testpass",
            is_test=True
        )
        
    def test_singleton_initialization(self):
        """Test singleton initialization."""
        # First initialization
        messenger1 = DirectMessenger(
            dsuserver="localhost",
            username="user1",
            password="pass1",
            is_test=True
        )
        
        # Verify instance attributes
        self.assertEqual(messenger1.dsuserver, "localhost")
        self.assertEqual(messenger1.username, "user1")
        self.assertEqual(messenger1.password, "pass1")
        self.assertIsNone(messenger1.token)
        self.assertIsNone(messenger1.socket)
        self.assertFalse(messenger1.connected)
        
    def test_connection_pool_management(self):
        """Test connection pool management."""
        # Mock socket operations
        with patch('socket.socket') as mock_socket:
            # Create multiple messengers with same server/port
            messenger1 = DirectMessenger(
                dsuserver="localhost",
                port=3001,
                username="user1",
                password="pass1",
                is_test=True
            )
            
            messenger2 = DirectMessenger(
                dsuserver="localhost",
                port=3001,
                username="user2",
                password="pass2",
                is_test=True
            )
            
            # Connect both - should use same connection
            messenger1._connect()
            messenger2._connect()
            
            # Verify only one socket was created
            self.assertEqual(mock_socket.call_count, 1)
            
            # Disconnect one - should keep connection
            messenger1._disconnect()
            self.assertTrue(messenger2.connected)
            
            # Disconnect last - should remove from pool
            messenger2._disconnect()
            self.assertEqual(len(messenger1._connection_pool), 0)
            
    def test_token_cache(self):
        """Test token caching and validation."""
        # Mock authentication response
        auth_response = {
            "response": {
                "type": "ok",
                "message": "Success",
                "token": "test-token"
            }
        }
        
        # Mock _receive to return auth response
        self.messenger._receive = Mock(return_value=json.dumps(auth_response))
        
        # First authentication
        self.assertTrue(self.messenger._authenticate())
        self.assertEqual(self.messenger.token, "test-token")
        
        # Verify token is cached
        with patch('time.time', return_value=time.time() + 1000):  # Within 24h
            self.assertTrue(self.messenger._is_token_valid())
            self.assertEqual(self.messenger.token, "test-token")
            
        # Expired token
        with patch('time.time', return_value=time.time() + 86401):  # >24h
            self.assertFalse(self.messenger._is_token_valid())
            
    def test_error_handling(self):
        """Test error handling in socket operations."""
        # Test connection error
        with self.assertRaises(ConnectionError):
            self.messenger._connect()
            
        # Test send error
        self.messenger.connected = True
        self.messenger.socket = Mock()
        self.messenger.socket.sendall.side_effect = socket.error
        with self.assertRaises(ConnectionError):
            self.messenger._send("test message")
            
        # Test receive error
        self.messenger._receive = Mock(side_effect=socket.error)
        with self.assertRaises(ConnectionError):
            self.messenger._receive()
            
    def test_message_parsing(self):
        """Test various message parsing scenarios."""
        # Test empty message list
        messages = self.messenger._parse_messages([])
        self.assertEqual(len(messages), 0)
        
        # Test single message
        test_messages = [{
            "message": "Hello",
            "from": "user1",
            "timestamp": 1234567890.0
        }]
        
        messages = self.messenger._parse_messages(test_messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, "Hello")
        self.assertEqual(messages[0].sender, "user1")
        
        # Test invalid message format
        invalid_messages = [{
            "invalid": "format"
        }]
        
        messages = self.messenger._parse_messages(invalid_messages)
        self.assertEqual(len(messages), 0)
        
    def test_thread_safety(self):
        """Test thread safety of operations."""
        import threading
        
        # Test concurrent connections
        def connect_messenger():
            messenger = DirectMessenger(
                dsuserver="localhost",
                port=3001,
                username="user" + str(threading.get_ident()),
                password="pass",
                is_test=True
            )
            messenger._connect()
            return messenger
        
        # Create multiple threads
        threads = []
        results = []
        
        for _ in range(5):
            t = threading.Thread(target=lambda: results.append(connect_messenger()))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
            
        # Verify all threads got the same instance
        first_messenger = results[0]
        for messenger in results[1:]:
            self.assertIs(messenger, first_messenger)


if __name__ == '__main__':
    unittest.main()
