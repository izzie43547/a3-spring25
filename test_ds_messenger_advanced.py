import unittest
import socket
import json
import time
from unittest.mock import Mock, patch
from ds_messenger import DirectMessenger


class TestDirectMessengerAdvanced(unittest.TestCase):
    """Advanced test cases for DirectMessenger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.messenger = DirectMessenger(
            dsuserver="localhost",
            username="testuser",
            password="testpass",
            is_test=True
        )
        
    def test_singleton_pattern(self):
        """
        Test that DirectMessenger implements singleton pattern correctly.
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
        
        # Both instances should be the same object
        self.assertIs(messenger1, messenger2)
        
        # Verify that the last initialization parameters are used
        self.assertEqual(messenger1.username, "user2")
        self.assertEqual(messenger1.password, "pass2")
        
    def test_connection_pooling(self):
        """
        Test connection pooling functionality.
        """
        # Mock socket creation
        with patch('socket.socket') as mock_socket:
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
                port=3002,
                username="user2",
                password="pass2",
                is_test=True
            )
            
            # Both should create new connections
            messenger1._connect()
            messenger2._connect()
            
            # Verify that two sockets were created
            self.assertEqual(mock_socket.call_count, 2)
            
            # Create another instance with same port as messenger1
            messenger3 = DirectMessenger(
                dsuserver="localhost",
                port=3001,
                username="user3",
                password="pass3",
                is_test=True
            )
            
            # This should reuse the existing connection
            messenger3._connect()
            self.assertEqual(mock_socket.call_count, 2)  # No new socket created
            
    def test_token_management(self):
        """
        Test token management and caching.
        """
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
        
        # First authentication should get a new token
        self.assertTrue(self.messenger._authenticate())
        self.assertEqual(self.messenger.token, "test-token")
        
        # Second authentication should reuse the cached token
        with patch('time.time', return_value=time.time() + 1000):  # Within 24h
            self.assertTrue(self.messenger._authenticate())
            self.assertEqual(self.messenger.token, "test-token")
            # _receive should only have been called once
            self.assertEqual(self.messenger._receive.call_count, 1)
        
        # After 24h, token should be expired and new one requested
        with patch('time.time', return_value=time.time() + 86401):  # >24h
            self.assertTrue(self.messenger._authenticate())
            self.assertEqual(self.messenger._receive.call_count, 2)
            
    def test_thread_safety(self):
        """
        Test thread safety of connection and token operations.
        """
        # Create multiple messengers in different threads
        import threading
        
        def create_messenger():
            return DirectMessenger(
                dsuserver="localhost",
                port=3001,
                username="user" + str(threading.get_ident()),
                password="pass",
                is_test=True
            )
        
        # Create 5 threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=create_messenger)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
            
        # All threads should have the same instance
        messenger1 = DirectMessenger(
            dsuserver="localhost",
            port=3001,
            username="user1",
            password="pass1",
            is_test=True
        )
        
        # Verify that all instances are the same
        for _ in range(5):
            messenger = DirectMessenger(
                dsuserver="localhost",
                port=3001,
                username="user2",
                password="pass2",
                is_test=True
            )
            self.assertIs(messenger, messenger1)


if __name__ == '__main__':
    unittest.main()
