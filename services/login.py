#login.py

#responsible for login functionality backend
import json
import os
import hashlib
import secrets


class LoginManager:
    """
    Manages user authentication and account creation.
    Passwords are hashed using SHA-256 with salt for security.
    """

    def __init__(self, data_file="user_data/accounts.json"):
        """Initialize the login manager with a data file path."""
        # Get the project root directory (BlueVault/)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.data_file = os.path.join(project_root, data_file)
        
        # Create user_data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        # Initialize file if it doesn't exist
        if not os.path.exists(self.data_file):
            self._save_data({})

    def _load_data(self):
        """Load user data from JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_data(self, data):
        """Save user data to JSON file."""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def _hash_password(self, password, salt=None):
        """
        Hash a password with a salt using SHA-256.
        
        Args:
            password: The password to hash
            salt: Optional salt (generated if not provided)
            
        Returns:
            tuple: (hashed_password, salt)
        """
        if salt is None:
            # Generate a random 32-byte salt
            salt = secrets.token_hex(32)
        
        # Combine password and salt, then hash
        password_salt = (password + salt).encode('utf-8')
        hashed = hashlib.sha256(password_salt).hexdigest()
        
        return hashed, salt

    def create_account(self, username, password):
        """
        Create a new user account.
        
        Args:
            username: The desired username
            password: The desired password
            
        Returns:
            tuple: (success: bool, message: str)
        """
        # Validation
        if not username or not password:
            return False, "Username and password cannot be empty."
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters."
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters."
        
        # Check if username already exists
        data = self._load_data()
        if username in data:
            return False, "Username already exists."
        
        # Hash the password with a unique salt
        hashed_password, salt = self._hash_password(password)
        
        # Store the account
        data[username] = {
            "password_hash": hashed_password,
            "salt": salt
        }
        self._save_data(data)
        
        return True, "Account created successfully."

    def verify_login(self, username, password):
        """
        Verify login credentials.
        
        Args:
            username: The username to verify
            password: The password to verify
            
        Returns:
            tuple: (success: bool, message: str)
        """
        # Validation
        if not username or not password:
            return False, "Username and password cannot be empty."
        
        # Load user data
        data = self._load_data()
        
        # Check if user exists
        if username not in data:
            return False, "Invalid username or password."
        
        # Get stored hash and salt
        stored_hash = data[username]["password_hash"]
        salt = data[username]["salt"]
        
        # Hash the provided password with the stored salt
        hashed_password, _ = self._hash_password(password, salt)
        
        # Compare hashes
        if hashed_password == stored_hash:
            return True, "Login successful."
        else:
            return False, "Invalid username or password."

    def user_exists(self, username):
        """Check if a username exists."""
        data = self._load_data()
        return username in data

    def get_all_usernames(self):
        """Get a list of all registered usernames (for debugging/admin purposes)."""
        data = self._load_data()
        return list(data.keys())


# Quick test if run directly
if __name__ == "__main__":
    print("--- Login Manager Test ---")
    
    # Create instance
    lm = LoginManager()
    
    # Test account creation
    success, msg = lm.create_account("testuser", "testpass123")
    print(f"Create account: {msg}")
    
    # Test login with correct password
    success, msg = lm.verify_login("testuser", "testpass123")
    print(f"Login (correct): {msg}")
    
    # Test login with wrong password
    success, msg = lm.verify_login("testuser", "wrongpass")
    print(f"Login (wrong): {msg}")
