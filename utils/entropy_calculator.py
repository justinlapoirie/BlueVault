"""
Shared password entropy calculation utilities.

Extracted from password_auditor.py so that the settings system (password
strength requirements on account creation) and the password auditor can
share one implementation.
"""

import math
import string


def calculate_entropy(password: str) -> float:
    """
    Calculate the Shannon-style entropy of a password in bits.

    Entropy = log2(pool_size) * length

    Pool size is determined by which character classes the password uses
    (lowercase, uppercase, digits, symbols).
    """
    if not password:
        return 0.0

    pool = 0
    if any(c in string.ascii_lowercase for c in password):
        pool += 26
    if any(c in string.ascii_uppercase for c in password):
        pool += 26
    if any(c in string.digits for c in password):
        pool += 10
    if any(c in string.punctuation for c in password):
        pool += 32

    if pool == 0:
        return 0.0

    return math.log2(pool) * len(password)


def determine_strength(entropy: float) -> str:
    """
    Convert an entropy value into a human-readable strength label.

    Returns:
        "Weak"     - entropy < 40
        "Moderate" - 40 <= entropy < 60
        "Strong"   - entropy >= 60
    """
    if entropy < 40:
        return "Weak"
    if entropy < 60:
        return "Moderate"
    return "Strong"


# Rank order used by meets_strength_requirement
_STRENGTH_RANK = {"Weak": 0, "Moderate": 1, "Strong": 2}


def meets_strength_requirement(password: str, requirement: str) -> tuple[bool, str]:
    """
    Check whether a password meets a configured strength requirement.

    Args:
        password: The candidate password.
        requirement: One of "off", "low", or "strong".
            - "off"    -> any non-empty password is accepted.
            - "low"    -> entropy rating must be Moderate or better.
            - "strong" -> entropy rating must be Strong.

    Returns:
        (ok, message). When ok is False, message explains why.
    """
    req = (requirement or "off").lower()

    if not password:
        return False, "Password cannot be empty."

    if req == "off":
        return True, "OK"

    entropy = calculate_entropy(password)
    score = determine_strength(entropy)
    rank = _STRENGTH_RANK[score]

    if req == "low":
        if rank >= _STRENGTH_RANK["Moderate"]:
            return True, "OK"
        return (
            False,
            "Password is too weak. Settings require at least a Moderate "
            f"strength password (current rating: {score}, entropy: "
            f"{entropy:.1f} bits).\n\nTry a longer password with a mix of "
            "upper/lowercase, digits, and symbols.",
        )

    if req == "strong":
        if rank >= _STRENGTH_RANK["Strong"]:
            return True, "OK"
        return (
            False,
            "Password does not meet the Strong strength requirement "
            f"(current rating: {score}, entropy: {entropy:.1f} bits).\n\n"
            "Use a longer password (typically 12+ characters) with a mix "
            "of upper/lowercase, digits, and symbols.",
        )

    # Unknown requirement - fail safe: accept
    return True, "OK"


# Quick test
if __name__ == "__main__":
    tests = ["", "abc", "password123", "Passw0rd!", "C0rrectHorseBatteryStaple!"]
    for p in tests:
        e = calculate_entropy(p)
        s = determine_strength(e)
        print(f"{p!r}: entropy={e:.2f}, strength={s}")
