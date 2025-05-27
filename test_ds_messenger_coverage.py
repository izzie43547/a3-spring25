import unittest
"""
Test cases for DirectMessenger coverage.

This module contains unit tests for the DirectMessenger class, focusing on
coverage of edge cases and internal functionality.
"""

import unittest
import json
import time
from unittest.mock import Mock, patch
from ds_messenger import DirectMessenger
import socket
import threading

class TestDirectMessengerCoverage(unittest.TestCase):
    """Test cases for DirectMessenger coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.messenger = DirectMessenger(
            dsuserver="localhost",
            username="testuser",
            password="testpass",
            is_test=True
        )

    def test_singleton_initialization(self):
        """Test singleton initialization.

        Verifies that DirectMessenger initializes correctly with the provided
        parameters and maintains proper state.
        """
        # First initialization
        messenger1 = DirectMessenger(
            dsuserver="localhost",
            username="user1",
            password="pass1",
            is_test=True
        )

        # Verify instance attributes
        self.assertEqual(messenger1.username, "user1")
        self.assertEqual(messenger1.password, "pass1")
        self.assertTrue(messenger1.is_test)
        self.assertFalse(messenger1.connected)
        self.assertIsNone(messenger1.token)
        self.assertIsNone(messenger1._connection_pool)

    def test_singleton_pattern(self):
        """Test that DirectMessenger implements singleton pattern correctly.

        Verifies that multiple instances of DirectMessenger share the same
        connection pool when using the same port.
        """
        # Create two instances with different parameters
        messenger1 = DirectMessenger(
            dsuserver="localhost",
            username="user1",
            password="pass1",
            is_test=True
        )

        messenger2 = DirectMessenger(
            dsuserver="localhost",
            username="user2",
            password="pass2",
            is_test=True
        )

        # Both should create new connections
        messenger1._connect()
        messenger2._connect()

        # Verify that two sockets were created
        self.assertEqual(len(messenger1._connection_pool), 2)
        self.assertEqual(len(messenger2._connection_pool), 2)

    def test_singleton_token_caching(self):
        """Test token caching in singleton pattern.

        Verifies that authentication tokens are cached and reused within
        the 24-hour validity period.
        """
        # First authentication
        auth_response = {
            "response": {
                "type": "ok",
                "message": "Success",
                "token": "test-token"
            }
        }

        # Mock _receive to return auth response
        self.messenger._receive = Mock(return_value=json.dumps(auth_response))

        # First authentication should get a new token
        self.assertTrue(self.messenger._authenticate())
        self.assertEqual(self.messenger.token, "test-token")

        # Second authentication should reuse the cached token
        with patch('time.time', return_value=time.time() + 1000):  # Within 24h
            self.assertTrue(self.messenger._authenticate())
            self.assertEqual(self.messenger.token, "test-token")

    def test_singleton_connection_pool(self):
        """Test connection pool management in singleton pattern.

        Verifies that multiple instances of DirectMessenger share the same
        connection pool when using the same port.
        """
        # Create two messengers with different ports
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
        self.assertEqual(len(messenger1._connection_pool), 1)
        self.assertEqual(len(messenger2._connection_pool), 1)

    def test_singleton_thread_safety(self):
        """Test thread safety of singleton pattern.

        Verifies that DirectMessenger can be safely used in a multi-threaded
        environment while maintaining proper connection pooling.
        """
        def connect_and_send(messenger):
            """Helper function to connect and send a message."""
            messenger._connect()
            messenger._send("test message")

        # Create 5 threads
        threads = []
        for _ in range(5):
            messenger = DirectMessenger(
                dsuserver="localhost",
                port=3001,
                username="user" + str(threading.get_ident()),
                password="pass",
                is_test=True
            )
            thread = Thread(target=connect_and_send, args=(messenger,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify that all instances are the same
        self.assertEqual(len(messenger._connection_pool), 1)

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
        with patch.object(self.messenger, '_parse_messages') as mock_parse:
            messages = self.messenger._parse_messages([])
            self.assertEqual(len(messages), 0)
            mock_parse.assert_called_once_with([])
        
        # Test single message
        test_messages = [{
            "message": "Hello",
            "from": "user1",
            "timestamp": 1234567890.0
        }]
        
        with patch.object(self.messenger, '_parse_messages') as mock_parse:
            messages = self.messenger._parse_messages(test_messages)
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].message, "Hello")
            self.assertEqual(messages[0].sender, "user1")
            mock_parse.assert_called_once_with(test_messages)
        
        # Test invalid message format
        invalid_messages = [{
            "invalid": "format"
        }]
        
        with patch.object(self.messenger, '_parse_messages') as mock_parse:
            messages = self.messenger._parse_messages(invalid_messages)
            self.assertEqual(len(messages), 0)
            mock_parse.assert_called_once_with(invalid_messages)
        
    def test_thread_safety(self):
        """Test thread safety of operations."""
        
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
