# ICS 32
# Assignment #1: Diary
#
# Author: Aaron Imani
#
# v0.1.0

# You should review this code to identify what features you need to support
# in your program for assignment 1.
#
# YOU DO NOT NEED TO READ OR UNDERSTAND THE JSON SERIALIZATION
# ASPECTS OF THIS CODE RIGHT NOW, though can you certainly
# take a look at it if you are curious since we already
# covered a bit of the JSON format in class.

import json
import time
from pathlib import Path


class NotebookFileError(Exception):
    """
    NotebookFileError is a custom exception handler that you should catch in your own code. It
    is raised when attempting to load or save Notebook objects to file the system.
    """
    pass

class IncorrectNotebookError(Exception):
    """
    NotebookError is a custom exception handler that you should catch in your own code. It
    is raised when attempting to deserialize a notebook file to a Notebook object.
    """
    pass


class Diary(dict):
    """
    The Diary class is responsible for working with individual user diaries.
    It currently supports two features: A timestamp property that is set upon
    instantiation and when the entry object is set and an entry property that
    stores the diary message.
    """
    def __init__(self, entry: str = None, timestamp: float = 0):
        self._timestamp = timestamp
        self.set_entry(entry)

        # Subclass dict to expose Diary properties for serialization
        # Don't worry about this!
        dict.__init__(self, entry=self._entry, timestamp=self._timestamp)
    
    def set_entry(self, entry):
        self._entry = entry
        self._timestamp = time.time()
        dict.__setitem__(self, 'entry', entry)
        dict.__setitem__(self, 'timestamp', self._timestamp)

    def get_entry(self):
        return self._entry
    
    def set_time(self, time: float):
        self._timestamp = time
        dict.__setitem__(self, 'timestamp', time)
    
    def get_timestamp(self):
        return self._timestamp

    """
    The property method is used to support get and set capability for entry and 
    time values. When the value for entry is changed, or set, the timestamp field is 
    updated to the current time.
    """ 
    entry = property(get_entry, set_entry)
    timestamp = property(get_timestamp, set_time)
    
    
class Notebook:
    """
    Notebook is a class that can be used to manage a diary notebook.
    """
    def __init__(self, username: str, password: str, bio: str):
        """Create a new Notebook object.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.
            bio (str): The bio of the user.
        """
        self.username = username
        self.password = password
        self.bio = bio
        self._diaries = []
    

    def add_diary(self, diary: Diary):
        """Add a new diary entry to the notebook.

        Args:
            diary (Diary): The diary entry to add.
        """
        self._diaries.append(diary)


    def del_diary(self, index: int) -> bool:
        """Delete a diary entry from the notebook.

        Args:
            index (int): The index of the diary entry to delete.

        Returns:
            bool: True if the diary was deleted, False otherwise.
        """
        if 0 <= index < len(self._diaries):
            del self._diaries[index]
            return True
        return False
        
    def get_diaries(self) -> list:
        """Get all diary entries.

        Returns:
            list: A list of all diary entries.
        """
        return self._diaries

    def save(self, path: str) -> None:
        """Save the notebook to a file.

        Args:
            path (str): The path to save the notebook to.
        """
        try:
            with open(path, 'w') as f:
                json.dump({
                    'username': self.username,
                    'password': self.password,
                    'bio': self.bio,
                    'diaries': [dict(d) for d in self._diaries]
                }, f, indent=4)
        except Exception as e:
            raise NotebookFileError(f"Failed to save notebook: {str(e)}")

    def load(self, path: str) -> None:
        """
        Populates the current instance of Notebook with data stored in a notebook file.

        Example usage: 

        ```
        notebook = Notebook()
        notebook.load('/path/to/file.json')
        ```

        Raises NotebookFileError, IncorrectNotebookError
        """
        p = Path(path)

        if p.exists() and p.suffix == '.json':
            try:
                f = open(p, 'r')
                obj = json.load(f)
                self.username = obj['username']
                self.password = obj['password']
                self.bio = obj['bio']
                for diary_obj in obj['_diaries']:
                    diary = Diary(diary_obj['entry'], diary_obj['timestamp'])
                    self._diaries.append(diary)
                f.close()
            except Exception as ex:
                raise IncorrectNotebookError(ex)
        else:
            raise NotebookFileError()
