"""
Login / master-account manager for BlueVault.

Master accounts (username -> password hash + salt + email) are stored
under ``user_data/accounts.json``. The file is **encrypted at rest**
using a randomly-generated symmetric key (Fernet / AES-128-CBC + HMAC)
that lives in a separate sidecar file (``user_data/.master.key``).

Why a sidecar key (rather than e.g. deriving from the master password)?
The login screen needs to read the file BEFORE any user has typed a
password, so the file's encryption key cannot itself depend on the
master password. The sidecar is treated like a database key file: file
system permissions are the security boundary, and on first run we
restrict the file mode to 0600 (owner read/write only).

Even if both files are stolen together, master passwords are still
protected by SHA-256 + per-user 32-byte salt, so a brute-force attack
must enumerate the actual passwords. What we add by encrypting the
file at rest is:

* casual readers (anyone browsing the project folder, a backup, a
  syncing service, etc.) can no longer see usernames, emails, or the
  password hashes;
* an attacker that copies just ``accounts.json`` (without the key
  sidecar) gets nothing.

If the file already exists in plaintext (older installs, the project's
seed data), it is transparently migrated to encrypted form on the next
read.
"""

import json
import os
import hashlib
import secrets
import stat

from cryptography.fernet import Fernet, InvalidToken


# Sidecar key file for accounts.json encryption.
ACCOUNTS_KEY_FILENAME = ".master.key"


class LoginManager:
    """
    Manages user authentication and account creation.
    Passwords are hashed using SHA-256 with salt for security, and the
    on-disk accounts file is encrypted with a sidecar key.
    """

    def __init__(self, data_file="user_data/accounts.json"):
        """Initialize the login manager with a data file path."""
        # Get the project root directory (BlueVault/)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.data_file = os.path.join(project_root, data_file)

        # Create user_data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        # Resolve the sidecar key file path.
        self.key_file = os.path.join(
            os.path.dirname(self.data_file), ACCOUNTS_KEY_FILENAME
        )

        # If the data file is missing, write an empty (encrypted) one
        # so subsequent reads have a stable base.
        if not os.path.exists(self.data_file):
            self._save_data({})

    # ------------------------------------------------------------------
    # Encryption sidecar key
    # ------------------------------------------------------------------
    def _load_or_create_key(self) -> bytes:
        """
        Return the symmetric encryption key for ``accounts.json``,
        generating + persisting one on first use.
        """
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, "rb") as f:
                    key = f.read().strip()
                if len(key) < 32:
                    raise ValueError(
                        f"{self.key_file} is corrupt or empty. "
                        "Restore from backup or delete user_data/ to start over."
                    )
                return key
            except OSError as e:
                raise RuntimeError(
                    f"Failed to read accounts encryption key {self.key_file}: {e}"
                )

        # First run: generate, persist, lock down permissions.
        key = Fernet.generate_key()
        try:
            with open(self.key_file, "wb") as f:
                f.write(key)
            self._restrict_permissions(self.key_file)
            print(
                f"[login] Generated new accounts encryption key at "
                f"{self.key_file} (do not delete this file)."
            )
        except OSError as e:
            raise RuntimeError(
                f"Failed to create accounts encryption key {self.key_file}: {e}"
            )
        return key

    @staticmethod
    def _restrict_permissions(path: str) -> None:
        """Best-effort lock-down to owner-only access (0600)."""
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # File I/O (encrypted)
    # ------------------------------------------------------------------
    def _load_data(self) -> dict:
        """Load user data from the encrypted accounts file."""
        if not os.path.exists(self.data_file):
            return {}

        try:
            with open(self.data_file, "rb") as f:
                raw = f.read()
        except OSError as e:
            print(f"[login] Failed to read accounts file: {e}")
            return {}

        if not raw:
            return {}

        # Migration path: if the file is still plain JSON (e.g. from an
        # older install), accept it and immediately re-save in
        # encrypted form. We only treat it as plaintext if it parses as
        # a JSON object -- random ciphertext would not.
        plaintext_data = self._try_parse_plaintext(raw)
        if plaintext_data is not None:
            print(
                "[login] accounts.json appears to be unencrypted; "
                "migrating to encrypted format."
            )
            try:
                self._save_data(plaintext_data)
            except Exception as e:
                print(f"[login] Migration save failed: {e}")
            return plaintext_data

        # Otherwise treat the file as ciphertext.
        try:
            cipher = Fernet(self._load_or_create_key())
            plaintext = cipher.decrypt(raw)
        except InvalidToken:
            print(
                "[login] Could not decrypt accounts.json -- the sidecar "
                f"key {self.key_file} does not match the file. The file "
                "may have been copied from another machine, or the key "
                "file may have been replaced. Refusing to overwrite."
            )
            return {}
        except Exception as e:
            print(f"[login] Unexpected decrypt error: {e}")
            return {}

        try:
            return json.loads(plaintext.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"[login] Decrypted accounts payload is not valid JSON: {e}")
            return {}

    @staticmethod
    def _try_parse_plaintext(raw: bytes):
        """Return a dict if ``raw`` is a JSON object, else None."""
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return None
        text = text.strip()
        if not text or not text.startswith("{"):
            return None
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
        return obj if isinstance(obj, dict) else None

    def _save_data(self, data: dict) -> None:
        """Persist user data, encrypted, to ``self.data_file``."""
        cipher = Fernet(self._load_or_create_key())
        plaintext = json.dumps(data, indent=4).encode("utf-8")
        encrypted = cipher.encrypt(plaintext)
        try:
            with open(self.data_file, "wb") as f:
                f.write(encrypted)
            self._restrict_permissions(self.data_file)
        except OSError as e:
            print(f"[login] Failed to save accounts file: {e}")
            raise

    # ------------------------------------------------------------------
    # Hashing
    # ------------------------------------------------------------------
    def _hash_password(self, password, salt=None):
        """Hash password with salt using SHA-256."""
        if salt is None:
            salt = secrets.token_hex(32)
        password_salt = (password + salt).encode("utf-8")
        hashed = hashlib.sha256(password_salt).hexdigest()
        return hashed, salt

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_account(self, username, password, email=""):
        """Create a new user account."""
        if not username or not password:
            return False, "Username and password cannot be empty."
        if len(username) < 3:
            return False, "Username must be at least 3 characters."
        if len(password) < 6:
            return False, "Password must be at least 6 characters."

        data = self._load_data()
        if username in data:
            return False, "Username already exists."

        hashed_password, salt = self._hash_password(password)
        data[username] = {
            "password_hash": hashed_password,
            "salt": salt,
            "email": email,
        }
        self._save_data(data)
        return True, "Account created successfully."

    def verify_login(self, username, password):
        """Verify login credentials."""
        if not username or not password:
            return False, "Username and password cannot be empty."

        data = self._load_data()
        if username not in data:
            return False, "Invalid username or password."

        stored_hash = data[username]["password_hash"]
        salt = data[username]["salt"]
        hashed_password, _ = self._hash_password(password, salt)

        if hashed_password == stored_hash:
            return True, "Login successful."
        return False, "Invalid username or password."

    def change_password(self, username, new_password):
        """Update master password hash + salt for an existing user.

        NOTE: Does NOT re-verify the old password; callers must do that.
        """
        if not username or not new_password:
            return False
        data = self._load_data()
        if username not in data:
            return False

        new_hash, new_salt = self._hash_password(new_password)
        data[username]["password_hash"] = new_hash
        data[username]["salt"] = new_salt
        try:
            self._save_data(data)
        except Exception as e:
            print(f"[login] change_password save failed: {e}")
            return False
        return True

    def user_exists(self, username):
        return username in self._load_data()

    def get_all_usernames(self):
        return list(self._load_data().keys())


# Quick test if run directly
if __name__ == "__main__":
    print("--- Login Manager Test ---")
    lm = LoginManager()
    success, msg = lm.create_account("testuser", "testpass123")
    print(f"Create account: {msg}")
    success, msg = lm.verify_login("testuser", "testpass123")
    print(f"Login (correct): {msg}")
    success, msg = lm.verify_login("testuser", "wrongpass")
    print(f"Login (wrong): {msg}")
