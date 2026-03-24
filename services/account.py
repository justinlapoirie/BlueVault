import json
import os
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import hashlib


class AccountManager:
    """
    Manages password vault entries with encryption.
    Each user gets their own vault file: vault_<username>.json
    """

    def __init__(self, username, master_password=None):
        """
        Initialize account manager for a specific user.

        Args:
            username: The logged-in user's username
            master_password: User's master password (used for encryption key derivation)
        """
        self.username = username
        self.vault_file = self._get_vault_path(username)

        # Derive encryption key from master password
        # In production, you'd want to use a proper key derivation function like PBKDF2
        if master_password:
            self.encryption_key = self._derive_key(master_password)
        else:
            # Fallback: use username as seed (less secure, but works without master password)
            self.encryption_key = self._derive_key(username)

        self.cipher = Fernet(self.encryption_key)

        # Create vault file if it doesn't exist
        if not os.path.exists(self.vault_file):
            self._initialize_vault()

    def _get_vault_path(self, username):
        """Get the path to the user's vault file."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        vault_dir = os.path.join(project_root, "user_data")
        os.makedirs(vault_dir, exist_ok=True)
        return os.path.join(vault_dir, f"vault_{username}.json")

    def _derive_key(self, password):
        """Derive an encryption key from a password."""
        # Use SHA-256 to create a 32-byte key from the password
        # In production, use PBKDF2 or similar with salt
        hash_obj = hashlib.sha256(password.encode('utf-8'))
        key = base64.urlsafe_b64encode(hash_obj.digest())
        return key

    def _initialize_vault(self):
        """Create a new empty vault file."""
        self._save_vault([])

    def _load_vault(self):
        """Load and decrypt the vault."""
        try:
            with open(self.vault_file, 'r') as f:
                encrypted_data = f.read()

            if not encrypted_data:
                return []

            # Decrypt the data
            decrypted_data = self.cipher.decrypt(encrypted_data.encode())
            accounts = json.loads(decrypted_data.decode())
            return accounts
        except Exception as e:
            print(f"Error loading vault: {e}")
            return []

    def _save_vault(self, accounts):
        """Encrypt and save the vault."""
        try:
            # Convert to JSON
            json_data = json.dumps(accounts, indent=2)

            # Encrypt the data
            encrypted_data = self.cipher.encrypt(json_data.encode())

            # Save to file
            with open(self.vault_file, 'wb') as f:
                f.write(encrypted_data)

            return True
        except Exception as e:
            print(f"Error saving vault: {e}")
            return False

    def create_account(self, account_name, username, password, notes="", website_url=""):
        """
        Create a new account entry.

        Args:
            account_name: Name of the account (e.g., "Netflix", "Gmail")
            username: Username or email for the account
            password: Password for the account
            notes: Optional notes
            website_url: Optional website URL

        Returns:
            dict: The created account entry with ID
        """
        accounts = self._load_vault()

        # Generate unique ID
        account_id = self._generate_id(accounts)

        # Create account entry
        now = datetime.now().isoformat()
        account = {
            "id": account_id,
            "account_name": account_name,
            "username": username,
            "password": password,  # Stored encrypted in vault
            "notes": notes,
            "website_url": website_url,
            "created_date": now,
            "last_password_change": now,
            "last_modified": now
        }

        accounts.append(account)

        if self._save_vault(accounts):
            return account
        else:
            return None

    def update_account(self, account_id, **kwargs):
        """
        Update an existing account entry.

        Args:
            account_id: ID of the account to update
            **kwargs: Fields to update (account_name, username, password, notes, website_url)

        Returns:
            dict: Updated account entry, or None if not found
        """
        accounts = self._load_vault()

        for account in accounts:
            if account["id"] == account_id:
                # Update fields
                for key, value in kwargs.items():
                    if key in account:
                        account[key] = value

                # Update last_modified timestamp
                account["last_modified"] = datetime.now().isoformat()

                # Update last_password_change if password was changed
                if "password" in kwargs:
                    account["last_password_change"] = datetime.now().isoformat()

                if self._save_vault(accounts):
                    return account
                else:
                    return None

        return None

    def delete_account(self, account_id):
        """
        Delete an account entry.

        Args:
            account_id: ID of the account to delete

        Returns:
            bool: True if deleted, False otherwise
        """
        accounts = self._load_vault()

        # Find and remove the account
        accounts = [acc for acc in accounts if acc["id"] != account_id]

        return self._save_vault(accounts)

    def get_account(self, account_id):
        """
        Get a specific account entry.

        Args:
            account_id: ID of the account

        Returns:
            dict: Account entry, or None if not found
        """
        accounts = self._load_vault()

        for account in accounts:
            if account["id"] == account_id:
                return account

        return None

    def get_all_accounts(self):
        """
        Get all account entries.

        Returns:
            list: List of all account entries
        """
        return self._load_vault()

    def _generate_id(self, accounts):
        """Generate a unique ID for a new account."""
        if not accounts:
            return 1

        max_id = max(acc["id"] for acc in accounts)
        return max_id + 1

    def get_password_age_days(self, account_id):
        """
        Get the number of days since password was last changed.

        Args:
            account_id: ID of the account

        Returns:
            int: Number of days since password change, or None if not found
        """
        account = self.get_account(account_id)

        if not account:
            return None

        last_change = datetime.fromisoformat(account["last_password_change"])
        now = datetime.now()
        delta = now - last_change

        return delta.days


# Quick test
if __name__ == "__main__":
    print("--- Account Manager Test ---")

    # Create manager for test user
    manager = AccountManager("testuser", "testpassword123")

    # Create an account
    account = manager.create_account(
        account_name="Test Account",
        username="test@example.com",
        password="securepass123",
        notes="This is a test",
        website_url="https://example.com"
    )
    print(f"Created account: {account['account_name']}")

    # Get all accounts
    all_accounts = manager.get_all_accounts()
    print(f"Total accounts: {len(all_accounts)}")

    # Update account
    if account:
        updated = manager.update_account(
            account["id"],
            notes="Updated notes"
        )
        print(f"Updated account: {updated['account_name']}")

    # Get password age
    if account:
        age = manager.get_password_age_days(account["id"])
        print(f"Password age: {age} days")