import os
import sys

# Ensure parent directory is importable so utils/ resolves when this file
# is run directly or imported from gui/.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.entropy_calculator import calculate_entropy, determine_strength


class PasswordAuditor:
    """
    A class for auditing password security.

    Features:
    - Checks for common passwords with a local list of the top 1,556 breached
      passwords (RockYou).
    - Calculates the entropy of the password to assess its strength.

    The entropy calculation and strength rating live in
    utils/entropy_calculator.py so that the settings system (password
    strength enforcement on account creation) and the auditor use one
    consistent implementation.
    """

    _BREACH_FILENAME = 'common_passwords.txt'

    def __init__(self, breach_file: str | None = None):
        self.breached_passwords = self._load_breached_password()

    # Main method to audit a password, returning a dictionary with the results
    def audit_password(self, password: str) -> dict:
        # Default report (minimums)
        report = {
            "entropy": 0,
            "score": "Weak",
            "warnings": [],
            "breached": False
        }
        # Empty password short-circuit
        if not password:
            report["warnings"].append("Password is empty.")
            return report
        # Check against breach list
        if password in self.breached_passwords:
            report["breached"] = True
            report["warnings"].append("Password has been found in a data breach.")
        # Calculate entropy and determine score (shared utility)
        entropy = calculate_entropy(password)
        report["entropy"] = entropy
        report["score"] = determine_strength(entropy)
        # Score / length warnings
        if report["score"] == "Weak":
            report["warnings"].append(
                "Password is weak. Consider using a longer password with a mix "
                "of character types."
            )
        if len(password) < 8:
            report["warnings"].append(
                "Password is too short. Minimum length should be at least 8 characters."
            )
        return report

    # Private method to load breached passwords txt file into a set for O(1) lookups
    def _load_breached_password(self) -> set:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, '..', 'utils', self._BREACH_FILENAME)
        bad_passwords = set()
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        bad_passwords.add(line.strip())
            else:
                print(f"Warning: Breached passwords file not found at {file_path}.")
        except Exception as e:
            print(f"Error loading breached passwords: {e}")
        return bad_passwords


# Quick test
if __name__ == "__main__":
    pa = PasswordAuditor()
    for pw in ["", "password", "Passw0rd!", "C0rrectHorseBatteryStaple!"]:
        print(pw, "->", pa.audit_password(pw))
