"""
a3.py

Main application for the Direct Messaging Chat assignment.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import json
import time
from datetime import datetime
from typing import List, Dict, Set, Optional
from pathlib import Path

# Import our DirectMessenger class
from ds_messenger import DirectMessenger, DirectMessage

class DirectMessengerGUI:
    """Graphical User Interface for the Direct Messaging application."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Direct Messaging Client")
        
        # Initialize DirectMessenger (not connected yet)
        self.messenger = None
        self.connected = False
        self.current_contact = None
        self.messages: Dict[str, List[DirectMessage]] = {}
        self.contacts: Set[str] = set()
        self.data_file = Path("messenger_data.json")
        
        # Configure the main window
        self._setup_ui()
        
        # Load saved data if available
        self._load_data()
        
        # Start the periodic message check
        self._check_messages()
    
    def _setup_ui(self):
        """Set up the user interface components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left panel (contacts)
        left_panel = ttk.Frame(main_frame, padding="5")
        left_panel.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W))
        
        # Contacts list
        contacts_label = ttk.Label(left_panel, text="Contacts")
        contacts_label.pack(fill=tk.X)
        
        self.contacts_tree = ttk.Treeview(left_panel, height=20, selectmode='browse', show='tree')
        self.contacts_tree.pack(fill=tk.Y)
        self.contacts_tree.bind('<<TreeviewSelect>>', self._on_contact_select)
        
        # Add contact button
        add_contact_btn = ttk.Button(
            left_panel, 
            text="Add Contact", 
            command=self._add_contact
        )
        add_contact_btn.pack(fill=tk.X, pady=5)
        
        # Right panel (chat)
        right_panel = ttk.Frame(main_frame, padding="5")
        right_panel.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            right_panel, 
            wrap=tk.WORD, 
            width=60, 
            height=20,
            state='disabled'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Message input
        msg_frame = ttk.Frame(right_panel)
        msg_frame.pack(fill=tk.X, pady=5)
        
        self.msg_entry = ttk.Entry(msg_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.msg_entry.bind('<Return>', lambda e: self._send_message())
        
        send_btn = ttk.Button(
            msg_frame, 
            text="Send", 
            command=self._send_message
        )
        send_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Login frame
        self.login_frame = ttk.LabelFrame(right_panel, text="Login", padding="10")
        self.login_frame.pack(fill=tk.X, pady=5)
        
        # Username
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Password
        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Login button
        login_btn = ttk.Button(
            self.login_frame,
            text="Login",
            command=self._login
        )
        login_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # Set focus to username entry
        self.username_entry.focus()
    
    def _login(self):
        """Handle login button click."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return
        
        try:
            # Initialize DirectMessenger with credentials
            self.messenger = DirectMessenger(
                username=username,
                password=password
            )
            
            # Test connection
            if not self.messenger.token:
                raise ConnectionError("Authentication failed")
            
            # Hide login frame
            self.login_frame.pack_forget()
            self.connected = True
            
            # Update UI
            self.root.title(f"Direct Messaging - {username}")
            
            # Load existing messages
            self._load_messages()
            
            # Update contacts list
            self._update_contacts_list()
            
        except Exception as e:
            messagebox.showerror("Login Failed", f"Could not connect: {str(e)}")
            if self.messenger:
                self.messenger = None
    
    def _add_contact(self):
        """Add a new contact to the list."""
        if not self.connected:
            messagebox.showinfo("Not Connected", "Please login first")
            return
        
        contact = simpledialog.askstring("Add Contact", "Enter username:")
        if contact and contact != self.messenger.username:
            self.contacts.add(contact)
            self._update_contacts_list()
            self._save_data()
    
    def _update_contacts_list(self):
        """Update the contacts list in the UI."""
        # Clear existing items
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)
        
        # Add contacts to the treeview
        for contact in sorted(self.contacts):
            self.contacts_tree.insert('', 'end', text=contact, values=(contact,))
    
    def _on_contact_select(self, event):
        """Handle contact selection."""
        selected = self.contacts_tree.selection()
        if not selected:
            return
        
        # Get the selected contact
        item = self.contacts_tree.item(selected[0])
        self.current_contact = item['text']
        
        # Display conversation with this contact
        self._display_conversation(self.current_contact)
    
    def _display_conversation(self, contact: str):
        """Display conversation with the specified contact."""
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        
        if contact in self.messages:
            for msg in sorted(self.messages[contact], key=lambda x: x.timestamp):
                self._display_message(msg)
        
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
    
    def _display_message(self, msg: DirectMessage):
        """Display a single message in the chat."""
        self.chat_display.config(state='normal')
        
        # Format timestamp
        time_str = datetime.fromtimestamp(msg.timestamp).strftime('%H:%M:%S')
        
        # Determine if it's an incoming or outgoing message
        if msg.sender == self.messenger.username:
            # Outgoing message
            prefix = f"You ({time_str}):"
            tag = "outgoing"
        else:
            # Incoming message
            prefix = f"{msg.sender} ({time_str}):"
            tag = "incoming"
        
        # Insert message with appropriate tag
        self.chat_display.insert(tk.END, f"{prefix}\n{msg.message}\n\n", tag)
        self.chat_display.tag_config("incoming", foreground="blue")
        self.chat_display.tag_config("outgoing", foreground="green")
        
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
    
    def _send_message(self):
        """Send a message to the current contact."""
        if not self.connected:
            messagebox.showinfo("Not Connected", "Please login first")
            return
        
        if not self.current_contact:
            messagebox.showinfo("No Contact Selected", "Please select a contact first")
            return
        
        message = self.msg_entry.get().strip()
        if not message:
            return
        
        try:
            # Send the message
            if self.messenger.send(message, self.current_contact):
                # Create a DirectMessage object for local storage
                msg = DirectMessage(
                    recipient=self.current_contact,
                    sender=self.messenger.username,
                    message=message,
                    timestamp=time.time()
                )
                
                # Add to messages
                if self.current_contact not in self.messages:
                    self.messages[self.current_contact] = []
                self.messages[self.current_contact].append(msg)
                
                # Update display
                self._display_message(msg)
                
                # Clear input
                self.msg_entry.delete(0, tk.END)
                
                # Save data
                self._save_data()
            else:
                messagebox.showerror("Error", "Failed to send message")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {str(e)}")
    
    def _check_messages(self):
        """Periodically check for new messages."""
        if self.connected and self.messenger:
            try:
                # Check for new messages
                new_messages = self.messenger.retrieve_new()
                
                # Process new messages
                for msg in new_messages:
                    sender = msg.sender
                    if sender not in self.contacts:
                        self.contacts.add(sender)
                        self._update_contacts_list()
                    
                    if sender not in self.messages:
                        self.messages[sender] = []
                    
                    # Add to messages if not already there
                    if not any(m.timestamp == msg.timestamp and m.message == msg.message 
                              for m in self.messages[sender]):
                        self.messages[sender].append(msg)
                        
                        # If this is the current contact, display the message
                        if self.current_contact == sender:
                            self._display_message(msg)
                
                # Save updated messages
                self._save_data()
                
            except Exception as e:
                print(f"Error checking messages: {str(e)}")
        
        # Schedule the next check
        self.root.after(5000, self._check_messages)
    
    def _save_data(self):
        """Save contacts and messages to a file."""
        data = {
            'contacts': list(self.contacts),
            'messages': {
                contact: [
                    {
                        'recipient': msg.recipient,
                        'sender': msg.sender,
                        'message': msg.message,
                        'timestamp': msg.timestamp
                    }
                    for msg in msgs
                ]
                for contact, msgs in self.messages.items()
            }
        }
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save data: {str(e)}")
    
    def _load_data(self):
        """Load contacts and messages from a file."""
        if not self.data_file.exists():
            return
            
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
                # Load contacts
                self.contacts = set(data.get('contacts', []))
                self._update_contacts_list()
                
                # Load messages
                self.messages = {
                    contact: [
                        DirectMessage(
                            recipient=msg['recipient'],
                            sender=msg['sender'],
                            message=msg['message'],
                            timestamp=msg['timestamp']
                        )
                        for msg in msgs
                    ]
                    for contact, msgs in data.get('messages', {}).items()
                }
                
        except Exception as e:
            print(f"Failed to load data: {str(e)}")
    
    def _load_messages(self):
        """Load all messages from the server."""
        if not self.connected or not self.messenger:
            return
        
        try:
            all_messages = self.messenger.retrieve_all()
            
            # Process all messages
            for msg in all_messages:
                # Determine the other party in the conversation
                if msg.sender == self.messenger.username:
                    # Outgoing message
                    contact = msg.recipient
                else:
                    # Incoming message
                    contact = msg.sender
                    self.contacts.add(contact)
                
                # Add to messages
                if contact not in self.messages:
                    self.messages[contact] = []
                
                # Add if not already in the list
                if not any(m.timestamp == msg.timestamp and m.message == msg.message 
                          for m in self.messages[contact]):
                    self.messages[contact].append(msg)
            
            # Update UI
            self._update_contacts_list()
            
            # Save the updated data
            self._save_data()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load messages: {str(e)}")

def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = DirectMessengerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
