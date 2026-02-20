import math
import string
import os

class PasswordAuditor:
    """
    A class for auditing password security.
    
    Features:
    - Checks for common passwords with a local list of the top 1,556 breached passwords. (RockYou)
    - Calculates Entropy of the password to assess its strength.
    """
    
    _BREACH_FILENAME = 'common_passwords.txt'

    def __init__(self, breach_file: str | None = None):
        # self._breach_filename = breach_file if breach_file else self._BREACH_FILENAME # Allow custom breach file path or default to the class constant
        self.breached_passwords = self._load_breached_password() # load breached password on initialization into a set

    # Main method to audit a password, returning a dictionary with the results
    def audit_password(self, password: str) -> dict:
        # Defult dictionary/report (minimums)
        report = {
            "entropy": 0,
            "score": "Weak",
            "warnings": [],
            "breached": False
        }
        # Check if password is empty before doing math
        if not password:
            report["warnings"].append("Password is empty.")
            return report
        # Check if password is in the breached passwords set
        if password in self.breached_passwords:
            report["breached"] = True
            report["warnings"].append("Password has been found in a data breach.")
        # Calculate entropy and determine score
        entropy = self._calculate_entropy(password)
        report["entropy"] = entropy
        report["score"] = self._determine_score(entropy)
        # Add warnings based on score and length
        if report["score"] == "Weak":
            report["warnings"].append("Password is weak. Consider using a longer password with a mix of character types.")
        if len(password) < 8:
            report["warnings"].append("Password is too short. Minimum length should be at least 8 characters.")
        return report



    # Private method to load breached passwords txt file into a set for O(1) lookups
    def _load_breached_password(self) -> set:
        current_dir = os.path.dirname(os.path.abspath(__file__)) # Get the directory of the current script
        file_path = os.path.join(current_dir, '..', 'utils', self._BREACH_FILENAME) # Construct the path to the breached passwords file
        bad_passwords = set()
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: # Open the file with error handling for encoding issues
                    for line in f:
                        bad_passwords.add(line.strip()) # Add each password to the set, stripping whitespace
            else:
                print(f"Warning: Breached passwords file not found at {file_path}.")
        except Exception as e:
            print(f"Error loading breached passwords: {e}")
        return bad_passwords
    
    # Private method to calculate the entropy of a password
    def _calculate_entropy(self, password: str) -> float:
        pool = 0
        if any(c in string.ascii_lowercase for c in password): pool += 26
        if any(c in string.ascii_uppercase for c in password): pool += 26
        if any(c in string.digits for c in password): pool += 10
        if any(c in string.punctuation for c in password): pool += 32
        if pool == 0:
            return 0.0
        return math.log2(pool) * len(password)
    
    # Private method to determine password strength in words based on entropy
    def _determine_score(self, entropy: float) -> str:
        if entropy < 40: return "Weak"
        if entropy < 60: return "Moderate"
        return "Strong"