"""
ds_protocol.py

Implementation of the Direct Messaging Protocol for ICS 32 Assignment 3.
"""

import json
import time
from collections import namedtuple
from typing import Dict, Any, Optional, List, Union

# Create a namedtuple to hold the values we expect to retrieve from json messages.
ServerResponse = namedtuple('ServerResponse', ['type', 'message', 'token', 'messages'])

class DSPProtocolError(Exception):
    """Custom exception for DSP protocol related errors."""
    pass

def format_auth_message(username: str, password: str) -> str:
    """
    Formats an authentication message to be sent to the server.
    
    Args:
        username: The username for authentication
        password: The password for authentication
        
    Returns:
        A JSON string representing the authentication message
    """
    auth_msg = {
        "authenticate": {
            "username": username,
            "password": password
        }
    }
    return json.dumps(auth_msg)

def format_direct_message(token: str, recipient: str, message: str) -> str:
    """
    Formats a direct message to be sent to another user.
    
    Args:
        token: The authentication token
        recipient: The recipient's username
        message: The message content
        
    Returns:
        A JSON string representing the direct message
    """
    direct_msg = {
        "token": token,
        "directmessage": {
            "message": message,  # Changed from 'entry' to 'message' to match server expectation
            "recipient": recipient,
            "timestamp": time.time()
        }
    }
    return json.dumps(direct_msg)

def format_fetch_request(token: str, fetch_type: str = 'all') -> str:
    """
    Formats a fetch request to retrieve messages.
    
    Args:
        token: The authentication token
        fetch_type: Type of messages to fetch ('all' or 'unread')
        
    Returns:
        A JSON string representing the fetch request
    """
    if fetch_type not in ['all', 'unread']:
        raise DSPProtocolError("Invalid fetch type. Must be 'all' or 'unread'")
    
    fetch_msg = {
        "token": token,
        "fetch": fetch_type
    }
    return json.dumps(fetch_msg)

def extract_json(json_msg: str) -> ServerResponse:
    """
    Extracts and validates the JSON response from the server.
    
    Args:
        json_msg: The JSON string received from the server
        
    Returns:
        A ServerResponse namedtuple containing the response data
        
    Raises:
        DSPProtocolError: If the JSON is invalid or missing required fields
    """
    try:
        json_obj = json.loads(json_msg)
        
        # Check if response exists and has required fields
        if 'response' not in json_obj:
            raise DSPProtocolError("Invalid server response: missing 'response' field")
            
        response = json_obj['response']
        
        # Extract response type and message
        resp_type = response.get('type')
        message = response.get('message', '')
        token = response.get('token')
        
        # Extract messages if they exist
        messages = response.get('messages', [])
        
        return ServerResponse(
            type=resp_type,
            message=message,
            token=token,
            messages=messages
        )
        
    except json.JSONDecodeError as e:
        raise DSPProtocolError(f"Failed to decode JSON: {str(e)}")
    except Exception as e:
        raise DSPProtocolError(f"Error processing server response: {str(e)}")

def is_valid_response(response: ServerResponse) -> bool:
    """
    Validates if the server response is successful.
    
    Args:
        response: The ServerResponse namedtuple
        
    Returns:
        bool: True if the response indicates success, False otherwise
    """
    return response.type == 'ok' if response else False
