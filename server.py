"""Server implementation for the Direct Messaging application.

This module implements a server that handles user authentication, message passing,
and user management for a direct messaging service.
"""
import socket
import threading
import json
from pathlib import Path
import sys
from datetime import datetime
import string
import secrets

# Configuration constants
USERS_PATH = 'users.json'
STORE_DIR_PATH = 'store'
# Set to False to disable debug output
DEBUG = True

# Server data storage structure:
# users.json contains user data with the following schema:
# {
#   "username": {
#       "password": "hashed_password",
#       "messages": [
#           {
#               "entry": "message text",
#               "from/recipient": "other_username",
#               "timestamp": "ISO timestamp",
#               "status": "unread|read"
#           }
#       ]
#   }
#}


def generate_token():
    """Generate a random token in the format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.
    
    Returns:
        str: A randomly generated token string.
    """
    return (
        f'{_generate_random_string(8)}-{_generate_random_string(4)}-'
        f'{_generate_random_string(4)}-{_generate_random_string(4)}-'
        f'{_generate_random_string(12)}'
    )

def _generate_random_string(n: int) -> str:
    """Generate a random alphanumeric string of specified length.
    
    Args:
        n: The length of the string to generate.
        
    Returns:
        str: A random alphanumeric string.
    """
    alphanums = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphanums) for _ in range(n))

# Global lock for thread-safe access to users file
users_file_lock = threading.Lock()


class DSUServer:
    """Server class for handling direct messaging functionality.
    
    This class manages user connections, authentication, and message passing
    between clients in a direct messaging application.
    """
    
    def __init__(self, host='127.0.0.1', port=3001):
        """Initialize the server with the given host and port.
        
        Args:
            host: The host address to bind to (default: '127.0.0.1')
            port: The port to listen on (default: 3001)
        """
        self.host = host
        self.port = port
        # Dictionary mapping tokens to usernames for active sessions
        self.sessions = {}
        # List of connected client sockets
        self.clients = []
    
    def start_server(self):
        """Start the server and listen for incoming connections."""
        # Create the store directory if it doesn't exist
        store_dir = Path(STORE_DIR_PATH)
        store_dir.mkdir(exist_ok=True)
        
        # Create users.json if it doesn't exist
        users_path = store_dir / USERS_PATH
        if not users_path.exists():
            with users_file_lock:
                with users_path.open('w') as f:
                    json.dump({}, f)
        
        # Create and configure the server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"Server started on {self.host}:{self.port}")
        
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address}")
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("Shutting down server...")
        finally:
            self.server_socket.close()
    
    def handle_client(self, client_socket, client_address):
        """Handle requests from a single client connection.
        
        Args:
            client_socket: The socket object for the client connection
            client_address: The address of the client (host, port)
        """
        current_user_token = None
        self.clients.append(client_socket)
        client_info = f"{client_address[0]}:{client_address[1]}"
        
        if DEBUG:
            print(f"New client connected: {client_info}")
            
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    if DEBUG:
                        print(f"Client {client_info} disconnected")
                    break
                    
                if DEBUG:
                    print(f"Message received by server: {repr(data)}")
                direct_message_read = False
                direct_message_sent = False
                msg = data.decode().strip() 
                if not msg:
                    if DEBUG:
                        print("Connection closed.")
                    break
                try:
                    command = json.loads(msg.strip())
                except json.JSONDecodeError:
                    message = 'Incorrectly formatted JSON message.'
                    status = 'error'
                else: 
                    message = ""
                    status = "error"
                    
                    if 'authenticate' in command:
                        
                        if len(command) != 1: 
                            status = "error"
                            message = "Incorrectly formatted authenticate command."
                        elif len(command['authenticate']) > 2:
                            status = "error"
                            message = "Extra fields provided to authenticate command object."
                        elif not all(field in command['authenticate'] for field in ['username', 'password']):
                            status = "error"
                            message = "Missing required fields for authenticate command object."
                        elif current_user_token:
                            status = "error"
                            message = "User already authenticated on the active session."
                        else:
                            ##execute authenticate command
                            
                            uname = command['authenticate']['username']
                            password = command['authenticate']['password']
                            
                            
                            fetched_user = self._get_or_create_new_user(uname, password)

                            current_user_token = generate_token()
                            if not fetched_user:
                                message = f'Welcome to ICS32 Distributed Social, {uname}!'
                                status = 'ok'
                                self.sessions[current_user_token] = uname

                                
                            else:
                                if fetched_user['password'] != password:
                                    status = "error"
                                    message = f'Incorrect password for the user {uname}'
                                    current_user_token = None
                                    
                                else:
                                    status = "ok"
                                    message = f'Welcome back, {uname}!'
                                    self.sessions[current_user_token] = uname
                    
                    ###direct message handling
                    elif 'directmessage' in command:
                        if 'token' not in command:
                            message = 'Missing token.'
                            status = 'error'
                        elif len(command) != 2:
                            message = "Incorrectly formatted directmessage command."
                            status = 'error'
                        else:
                            dm_data = command['directmessage']
                            if not isinstance(dm_data, dict) or 'recipient' not in dm_data or 'message' not in dm_data:
                                message = "Missing required fields for direct message (recipient, message)."
                                status = 'error'
                            else:
                                token = command['token']
                                if token == current_user_token and token in self.sessions:
                                    current_user = self.sessions[token]
                                    recipient = dm_data['recipient']
                                    # Make sure we're using the correct field name
                                    message_content = dm_data.get('message') or dm_data.get('entry', '')
                                    timestamp = str(datetime.now().timestamp())
                                    direct_message_sent = True
                                    
                                    if self._send_message(message_content, current_user, recipient, timestamp):
                                        message = 'Direct message sent'
                                        status = 'ok'
                                    else:
                                        message = 'Unable to send direct message. Recipient may not exist.'
                                        status = 'error'
                                else:
                                    message = 'Invalid user token.'
                                    status = 'error'
                            
                    elif 'fetch' in command:
                        args = command['fetch']
                        token = command['token']
                        if args == 'all':
                            if token == current_user_token and token in self.sessions:
                                current_user = self.sessions[token]
                                direct_message_read = True
                                message = self._read_all_messages(current_user)
                                status = 'ok'
                            else:
                                message = f'Invalid user token.'
                                status = 'error'
                        elif args == 'unread':
                            if token == current_user_token and token in self.sessions:
                                current_user = self.sessions[token]
                                direct_message_read = True
                                message = self._read_unread_messages(current_user)
                                status = 'ok'
                            else:
                                message = f'Invalid user token.'
                                status = 'error'

                        else:
                            message = 'Invalid argument for fetch field.'
                            status = 'error'

                    else:
                        message = 'Invalid command.'
                        status = 'error'
                if DEBUG:
                    print(f'Server sending the following message: "{message}"')
                if direct_message_read:
                    resp = {'response': {'type':status, 'messages': message} }
                elif direct_message_sent:
                    resp = {'response': {'type':status, 'message': message} }
                elif status == 'ok':
                    resp = {'response': {'type':status, 'message': message, 'token': current_user_token} }
                else:
                    resp = {'response': {'type':status, 'message': message}}
                json_response = json.dumps(resp).encode()
                client_socket.sendall(json_response + b'\r\n')
            if current_user_token and current_user_token in self.sessions:
                del self.sessions[current_user_token]
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
            self.clients.remove(client_socket)
            
    def _send_message(self, entry, username, recipient, timestamp=''):
        """Send a message from one user to another.
        
        Args:
            entry: The message content
            username: Sender's username
            recipient: Recipient's username
            timestamp: Optional timestamp (defaults to current time if not provided)
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        with users_file_lock:
            users_path = Path('.') / STORE_DIR_PATH / Path(USERS_PATH)
            existing_users = None
            with users_path.open('r') as user_file:
                existing_users = json.load(user_file)
            
            fetched_sender = existing_users.get(username, None)
            fetched_user = existing_users.get(recipient, None)
            if not fetched_sender:
                return False
            if not fetched_user:
                return False
            
            else:
                with users_path.open('w') as user_file:
                    fetched_sender['messages'].append({'message': entry, 'recipient': recipient, 'timestamp': timestamp, 'status': 'sent'})
                    fetched_user['messages'].append({'message': entry, 'from': username, 'timestamp': timestamp, 'status': 'unread'})
                    existing_users[recipient] = fetched_user
                    existing_users[username] = fetched_sender
                    json.dump(existing_users, user_file)
        return True

    def _read_all_messages(self, username):
        """Retrieve all messages for a given user.
        
        Args:
            username: The username to retrieve messages for
            
        Returns:
            list: List of messages or empty list if user not found
        """
        with users_file_lock:
            users_path = Path('.') / STORE_DIR_PATH / Path(USERS_PATH)
            existing_users = None
            with users_path.open('r') as user_file:
                existing_users = json.load(user_file)

            fetched_user = existing_users.get(username, None)
            if not fetched_user:
                return False ##double check that user exists
            result = []
            for message in fetched_user['messages']:
                if 'from' in message:
                    mod_message = {'from': message['from'], 'message': message['message'], 'timestamp': message['timestamp']}
                else:
                    mod_message = {'recipient': message['recipient'], 'message': message['message'], 'timestamp': message['timestamp']}
                result.append(mod_message)
                if message['status'] == 'unread':
                    message['status'] = 'read'

            else:
                with users_path.open('w') as user_file:
                    
                    existing_users[username] = fetched_user
                    json.dump(existing_users, user_file)
            
            return sorted(result, key=lambda x: float(x["timestamp"]))

    
    def _read_unread_messages(self, username):
        """Retrieve all unread messages for a given user.
        
        Args:
            username: The username to retrieve unread messages for
            
        Returns:
            list: List of unread messages or empty list if user not found
        """
        with users_file_lock:
            users_path = Path('.') / STORE_DIR_PATH / Path(USERS_PATH)
            existing_users = None
            with users_path.open('r') as user_file:
                existing_users = json.load(user_file)

            fetched_user = existing_users.get(username, None)
            if not fetched_user:
                return False ##double check that user exists
            result = []
            for message in fetched_user['messages']:
                if message['status'] == 'unread':
                    mod_message = {'from': message['from'], 'message': message['message'], 'timestamp': message['timestamp']}
                    result.append(mod_message)
                    message['status'] = 'read'
            
            
            else:
                with users_path.open('w') as user_file:
                    existing_users[username] = fetched_user
                    
            fetched_user = existing_users.get(username, None)
            if fetched_user:
                return fetched_user
            else:
                with users_path.open('w') as user_file:
                    
                    fetched_user = existing_users.get(username, None)
                    if fetched_user: ##double check that no user exists
                        return False
                    else:
                        existing_users.update({username: {'password': password, 'bio': {"entry": "", "timestamp": ""}, 'posts': [], 'messages':[]}})
                    json.dump(existing_users, user_file)
            
        
    def _create_storage_system(self):
        """Create the local storage system if it doesn't exist.
        
        Creates a directory called "store" with users.json file if they
        don't already exist.
        """
        users_path = Path('.') / STORE_DIR_PATH / Path(USERS_PATH)
        store_path = Path('.') / Path(STORE_DIR_PATH)
        store_path.mkdir(exist_ok=True)
        if not users_path.exists():
            with users_path.open('w') as json_file:
                json.dump({}, json_file, indent=4)

    def start_server(self):
        '''Starts the server (hence the name of the method :))'''
        self._create_storage_system() #does nothing if the server store files exists already
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
                srv.bind((self.host, self.port))
                srv.listen(5)
                if DEBUG:
                    print("DSUserver is listening on port", self.port)
                while True:
                    connection, address = srv.accept()
                    client_handler = threading.Thread(target = self.handle_client, args = (connection,address))
                    client_handler.start()
        except KeyboardInterrupt as e:
            if DEBUG:
                print(f'Server shutting down...')
        finally:
            for conn in self.clients:
                conn.close()
            self.clients = []
            if DEBUG:
                print('Disconnected all clients.')

        
def run_server(host = '127.0.0.1', port1 = 3001):
    try:
        server = DSUServer(host, port1)
        server.start_server()
    except Exception as e:
        print(f'Server raised the following error:{e}')
    
if __name__ == '__main__':
    host = '127.0.0.1'
    port1 = 3001
    port2 = 3002
    if len(sys.argv) >= 2:
        port1 = int(sys.argv[1])
   
    run_server(host,port1)


