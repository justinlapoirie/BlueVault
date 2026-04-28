"""
Settings management backend for BlueVault.

Each user has a per-user settings JSON file stored in user_data/
(settings_<username>.json). The SettingsManager loads and persists these
settings and also implements the higher-level vault operations that the
settings UI exposes (change master password, export vault, import vault).
"""

import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime


# -----------------------------------------------------------------------------
# Defaults and allowed option tables
# -----------------------------------------------------------------------------

DEFAULT_SETTINGS = {
    # Seconds of inactivity before auto-logout (0 disables -> treated as default)
    "auto_logout_time": 300,          # 5 minutes
    # Days before the account card turns colored / prompts for renewal (0 = off)
    "password_renewal_days": 0,       # off by default
    # Seconds before clipboard auto-clears after a copy (0 = never)
    "clipboard_autoclear_seconds": 60,
    # Password strength enforcement on account creation: "off" | "low" | "strong"
    "password_strength_requirement": "off",
    # How the main menu sorts account cards
    # "alphabetical" | "date_created" | "date_modified" | "last_copied"
    "account_sort_by": "alphabetical",
}

AUTO_LOGOUT_OPTIONS = {
    "2 minutes": 120,
    "5 minutes": 300,
    "10 minutes": 600,
}

PASSWORD_RENEWAL_OPTIONS = {
    "Off": 0,
    "7 days": 7,
    "30 days": 30,
    "90 days": 90,
}

CLIPBOARD_AUTOCLEAR_OPTIONS = {
    "30 seconds": 30,
    "1 minute": 60,
    "5 minutes": 300,
    "Never": 0,
}

PASSWORD_STRENGTH_OPTIONS = {
    "Off": "off",
    "Low": "low",
    "Strong": "strong",
}

SORT_BY_OPTIONS = {
    "Alphabetical": "alphabetical",
    "Date Created": "date_created",
    "Date Modified": "date_modified",
    "Last Copied": "last_copied",
}


class SettingsManager:
    """
    Manage per-user settings and vault-level operations driven by the
    settings UI (password change, export, import).
    """

    def __init__(self, username: str):
        self.username = username
        self.settings_file = self._get_settings_path(username)
        self.settings = self._load_settings()

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------
    def _project_root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _user_data_dir(self) -> str:
        path = os.path.join(self._project_root(), "user_data")
        os.makedirs(path, exist_ok=True)
        return path

    def _get_settings_path(self, username: str) -> str:
        return os.path.join(self._user_data_dir(), f"settings_{username}.json")

    def _vault_path(self, username: str) -> str:
        return os.path.join(self._user_data_dir(), f"vault_{username}.json")

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------
    def _load_settings(self) -> dict:
        """Load settings from disk, filling in defaults for missing keys."""
        if not os.path.exists(self.settings_file):
            merged = dict(DEFAULT_SETTINGS)
            self._write_settings(merged)
            print(
                f"[settings] No settings file for {self.username!r}; "
                f"created defaults at {self.settings_file}"
            )
            return merged

        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[settings] Failed to load {self.settings_file}: {e}")
            data = {}

        # Fill in any missing keys with defaults
        merged = dict(DEFAULT_SETTINGS)
        merged.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
        print(f"[settings] Loaded for {self.username!r}: {merged}")
        return merged

    def _write_settings(self, data: dict) -> bool:
        try:
            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=4)
            print(f"[settings] Wrote {self.settings_file}: {data}")
            return True
        except OSError as e:
            print(f"[settings] Failed to save {self.settings_file}: {e}")
            return False

    def save(self) -> bool:
        """Persist the current in-memory settings."""
        return self._write_settings(self.settings)

    # ------------------------------------------------------------------
    # Generic getters / setters
    # ------------------------------------------------------------------
    def get(self, key: str):
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key: str, value) -> None:
        if key in DEFAULT_SETTINGS:
            self.settings[key] = value

    # ------------------------------------------------------------------
    # Typed getters used by the rest of the app
    # ------------------------------------------------------------------
    def get_auto_logout_time(self) -> int:
        return int(self.settings.get("auto_logout_time", DEFAULT_SETTINGS["auto_logout_time"]))

    def get_password_renewal_days(self) -> int:
        return int(self.settings.get("password_renewal_days", DEFAULT_SETTINGS["password_renewal_days"]))

    def get_clipboard_autoclear_seconds(self) -> int:
        return int(self.settings.get("clipboard_autoclear_seconds", DEFAULT_SETTINGS["clipboard_autoclear_seconds"]))

    def get_password_strength_requirement(self) -> str:
        return str(self.settings.get("password_strength_requirement", DEFAULT_SETTINGS["password_strength_requirement"]))

    def get_account_sort_by(self) -> str:
        return str(self.settings.get("account_sort_by", DEFAULT_SETTINGS["account_sort_by"]))

    # ------------------------------------------------------------------
    # Master password change
    # ------------------------------------------------------------------
    def change_master_password(self, login_manager, old_password: str,
                               new_password: str, confirm_password: str):
        """
        Change the user's master password and re-encrypt their vault.

        Args:
            login_manager: a LoginManager instance.
            old_password: current master password.
            new_password: desired new master password.
            confirm_password: must equal new_password.

        Returns:
            (success: bool, message: str)
        """
        from services.account import AccountManager

        if not new_password or not confirm_password:
            return False, "New password fields cannot be empty."
        if new_password != confirm_password:
            return False, "New password and confirmation do not match."
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters."
        if new_password == old_password:
            return False, "New password must be different from the current password."

        # Verify current password
        ok, msg = login_manager.verify_login(self.username, old_password)
        if not ok:
            return False, "Current password is incorrect."

        # Load the decrypted vault with the old key
        try:
            old_am = AccountManager(self.username, old_password)
            accounts = old_am._load_vault()
        except Exception as e:
            return False, f"Failed to decrypt current vault: {e}"

        # Update credentials in the login store
        try:
            ok = login_manager.change_password(self.username, new_password)
            if not ok:
                return False, "Failed to update stored credentials."
        except Exception as e:
            return False, f"Failed to update stored credentials: {e}"

        # Re-encrypt the vault with the new key
        try:
            new_am = AccountManager(self.username, new_password)
            if not new_am._save_vault(accounts):
                return False, "Failed to re-encrypt vault with new password."
        except Exception as e:
            return False, f"Failed to re-encrypt vault: {e}"

        return True, "Master password changed successfully."

    # ------------------------------------------------------------------
    # Export / Import vault
    # ------------------------------------------------------------------
    def _downloads_dir(self) -> str:
        """Best-effort locate the user's Downloads directory."""
        home = os.path.expanduser("~")
        candidate = os.path.join(home, "Downloads")
        if os.path.isdir(candidate):
            return candidate
        return home  # fallback

    def export_vault(self, master_password: str, destination: str | None = None):
        """
        Bundle the user's (already-encrypted) vault file plus a small
        manifest into a zip in the user's Downloads directory.

        Args:
            master_password: verifies the user can actually decrypt the
                             vault before we export anything.
            destination: optional override for output folder.

        Returns:
            (success: bool, message_or_path: str)
        """
        from services.account import AccountManager

        # Sanity check: ensure the password decrypts the vault
        try:
            am = AccountManager(self.username, master_password)
            _ = am._load_vault()
        except Exception as e:
            return False, f"Cannot decrypt vault with provided password: {e}"

        vault_path = self._vault_path(self.username)
        if not os.path.exists(vault_path):
            return False, "No vault file to export."

        out_dir = destination or self._downloads_dir()
        os.makedirs(out_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"bluevault_export_{self.username}_{timestamp}.zip"
        zip_path = os.path.join(out_dir, zip_name)

        manifest = {
            "app": "BlueVault",
            "version": 1,
            "username": self.username,
            "exported_at": datetime.now().isoformat(),
        }

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(vault_path, arcname=f"vault_{self.username}.json")
                zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        except Exception as e:
            return False, f"Failed to write export zip: {e}"

        return True, zip_path

    def import_vault(self, zip_path: str, master_password: str,
                     mode: str = "append"):
        """
        Import an exported BlueVault zip into the current user's vault.

        Args:
            zip_path: path to the exported .zip
            master_password: current user's master password (must match
                             the exporter's password because the same key
                             is derived from it; we also verify the
                             embedded username matches this user).
            mode: "override" to replace, "append" to merge unique entries.

        Returns:
            (success: bool, message: str)
        """
        from services.account import AccountManager

        if mode not in ("override", "append"):
            return False, f"Unknown import mode: {mode}"
        if not os.path.isfile(zip_path):
            return False, "Import file not found."

        # Extract zip contents to a temp directory
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                if "manifest.json" not in names:
                    return False, "Import file is missing manifest.json."
                with zf.open("manifest.json") as mf:
                    manifest = json.loads(mf.read().decode("utf-8"))

                expected_vault_name = f"vault_{manifest.get('username', '')}.json"
                if expected_vault_name not in names:
                    return False, (
                        "Import file is missing the expected vault entry "
                        f"({expected_vault_name})."
                    )

                # Verify username matches the current user
                if manifest.get("username") != self.username:
                    return False, (
                        "Master login mismatch: exported vault belongs to "
                        f"'{manifest.get('username')}', but you are logged "
                        f"in as '{self.username}'."
                    )

                # Extract vault file to temp
                tmpdir = tempfile.mkdtemp(prefix="bluevault_import_")
                try:
                    zf.extract(expected_vault_name, tmpdir)
                    extracted_path = os.path.join(tmpdir, expected_vault_name)

                    # Try to decrypt with current master password.
                    # We temporarily swap in the extracted vault by pointing
                    # a new AccountManager at it, then reading its contents.
                    imported_accounts = self._decrypt_vault_file(
                        extracted_path, master_password
                    )
                    if imported_accounts is None:
                        return False, (
                            "Could not decrypt imported vault. The master "
                            "password on this device does not match the "
                            "password used when the vault was exported."
                        )
                finally:
                    shutil.rmtree(tmpdir, ignore_errors=True)
        except zipfile.BadZipFile:
            return False, "Import file is not a valid zip."
        except Exception as e:
            return False, f"Failed to read import file: {e}"

        # Now merge / override into the current user's vault
        try:
            current_am = AccountManager(self.username, master_password)
            current = current_am._load_vault()

            if mode == "override":
                new_vault = list(imported_accounts)
                # Re-number ids cleanly
                for i, acc in enumerate(new_vault, start=1):
                    acc["id"] = i
                merged_count = len(new_vault)
                ok = current_am._save_vault(new_vault)
                if not ok:
                    return False, "Failed to write imported vault."
                return True, f"Override complete. Replaced vault with {merged_count} accounts."

            # Append mode - only add accounts whose (account_name, username)
            # are not already present in the current vault.
            existing_keys = {
                (acc.get("account_name", "").lower(),
                 acc.get("username", "").lower())
                for acc in current
            }
            next_id = max((acc.get("id", 0) for acc in current), default=0) + 1

            added = 0
            for acc in imported_accounts:
                key = (acc.get("account_name", "").lower(),
                       acc.get("username", "").lower())
                if key in existing_keys:
                    continue
                new_acc = dict(acc)
                new_acc["id"] = next_id
                next_id += 1
                # Ensure last_copied key exists
                new_acc.setdefault("last_copied", None)
                current.append(new_acc)
                existing_keys.add(key)
                added += 1

            ok = current_am._save_vault(current)
            if not ok:
                return False, "Failed to write merged vault."
            return True, f"Append complete. Added {added} new account(s)."
        except Exception as e:
            return False, f"Import failed: {e}"

    @staticmethod
    def _decrypt_vault_file(vault_file_path: str, master_password: str):
        """Attempt to decrypt an exported vault file; return list or None."""
        import base64
        import hashlib
        from cryptography.fernet import Fernet, InvalidToken

        try:
            with open(vault_file_path, "r") as f:
                encrypted = f.read()
        except OSError:
            return None

        if not encrypted:
            return []

        key = base64.urlsafe_b64encode(
            hashlib.sha256(master_password.encode("utf-8")).digest()
        )
        cipher = Fernet(key)

        try:
            decrypted = cipher.decrypt(encrypted.encode())
            return json.loads(decrypted.decode())
        except (InvalidToken, ValueError, json.JSONDecodeError):
            return None


# Quick test
if __name__ == "__main__":
    sm = SettingsManager("testuser")
    print("Loaded settings:", sm.settings)
    sm.set("auto_logout_time", 600)
    sm.save()
    print("After save:", sm.settings)
