# Direct Messaging Chat Application

A direct messaging client application that allows users to send and receive messages in real-time using a client-server architecture.

## Features

- User authentication
- Add/remove contacts
- Send and receive direct messages
- View message history
- Real-time message updates
- Persistent storage of messages and contacts

## Prerequisites

- Python 3.7 or higher
- Required Python packages (install using `pip install -r requirements.txt`):
  - tkinter (usually comes with Python)
  - json
  - pathlib
  - datetime
  - time
  - socket

## Project Structure

```
a3-starter-spring25/
├── a3.py                 # Main application (GUI)
├── ds_messenger.py      # Direct messaging client implementation
├── ds_protocol.py       # Protocol implementation
├── server.py            # Server implementation for testing
├── test_ds_messenger.py # Unit tests for ds_messenger.py
├── test_ds_message_protocol.py  # Unit tests for ds_protocol.py
└── README.md            # This file
```

## Running the Application

1. Start the server (in a separate terminal):
   ```
   python server.py
   ```

2. Run the client application:
   ```
   python a3.py
   ```

3. Log in with your username and password

## Testing

Run the test suite using pytest:

```
python -m pytest test_ds_message_protocol.py -v
python -m pytest test_ds_messenger.py -v
```

## Usage

1. **Login**: Enter your username and password to connect to the server
2. **Add Contacts**: Click "Add Contact" and enter the username of the person you want to message
3. **Send Messages**: Select a contact, type your message, and press Enter or click Send
4. **View Messages**: Click on a contact to view your conversation history

## Implementation Details

- **ds_protocol.py**: Implements the DSP (Direct Server Protocol) for message formatting and parsing
- **ds_messenger.py**: Handles client-side messaging functionality and server communication
- **a3.py**: Implements the Tkinter-based GUI for the messaging client
- **server.py**: A simple server implementation for testing the client

## Error Handling

The application includes error handling for:
- Network connectivity issues
- Invalid user input
- Server communication errors
- File I/O errors for local storage

## Known Issues

- The server implementation is basic and not production-ready
- No message encryption is implemented
- Limited error recovery in some edge cases

## Future Improvements

- Implement message encryption
- Add support for group chats
- Add message read receipts
- Improve error handling and recovery
- Add support for file attachments
- Implement user status (online/offline)

## License

This project is for educational purposes only.
