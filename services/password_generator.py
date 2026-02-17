import secrets
import string


class PasswordGenerator:
    """
    A class for generating secure, customizable passwords.

    Default settings can be configured at instantiation and overridden
    per-call in generate_password(), making it easy to reuse across files.

    Example usage from another file:
        from password_generator import PasswordGenerator

        pg = PasswordGenerator(length=16, include_symbols=False)
        password = pg.generate_password()

        # Or override defaults for a single call:
        password = pg.generate_password(length=20, include_symbols=True)
    """

    # Character sets as a class-level constant — shared across all instances
    _CHAR_SETS = {
        "uppercase": string.ascii_uppercase,
        "lowercase": string.ascii_lowercase,
        "digits": string.digits,
        "symbols": string.punctuation,
    }

    _MIN_LENGTH = 7

    def __init__(
        self,
        length: int = 12,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_symbols: bool = True,
    ):
        """Store default settings for this generator instance."""
        self._length = length
        self._include_uppercase = include_uppercase
        self._include_lowercase = include_lowercase
        self._include_digits = include_digits
        self._include_symbols = include_symbols

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_password(
        self,
        length: int | None = None,
        include_uppercase: bool | None = None,
        include_lowercase: bool | None = None,
        include_digits: bool | None = None,
        include_symbols: bool | None = None,
    ) -> str:
        """
        Generate and return a secure password.

        Any parameter left as None falls back to the instance default
        set in __init__, so callers only need to pass what they want to
        override.
        """
        # Resolve effective settings (per-call overrides take priority)
        length = length if length is not None else self._length
        use_upper = include_uppercase if include_uppercase is not None else self._include_uppercase
        use_lower = include_lowercase if include_lowercase is not None else self._include_lowercase
        use_digits = include_digits if include_digits is not None else self._include_digits
        use_symbols = include_symbols if include_symbols is not None else self._include_symbols

        self._validate_length(length)

        allowed_characters, required_chars = self._build_character_pool(
            use_upper, use_lower, use_digits, use_symbols
        )

        if not allowed_characters:
            raise ValueError("At least one character type must be included.")
        if length < len(required_chars):
            raise ValueError(
                f"Password length must be at least {len(required_chars)} "
                "characters to include all selected character types."
            )

        return self._assemble_password(length, allowed_characters, required_chars)


    # Private helpers
    def _validate_length(self, length: int) -> None:
        """Raise ValueError if length is below the minimum threshold."""
        if length < self._MIN_LENGTH:
            raise ValueError(
                f"Password length must be at least {self._MIN_LENGTH} characters."
            )

    def _build_character_pool(
        self,
        use_upper: bool,
        use_lower: bool,
        use_digits: bool,
        use_symbols: bool,
    ) -> tuple[str, list[str]]:
        """
        Build the pool of allowed characters and the list of guaranteed
        required characters (one per selected category).
        """
        allowed_characters = ""
        required_chars = []

        selections = [
            (use_upper, "uppercase"),
            (use_lower, "lowercase"),
            (use_digits, "digits"),
            (use_symbols, "symbols"),
        ]

        for enabled, key in selections:
            if enabled:
                char_set = self._CHAR_SETS[key]
                allowed_characters += char_set
                required_chars.append(secrets.choice(char_set))

        return allowed_characters, required_chars

    def _assemble_password(
        self,
        length: int,
        allowed_characters: str,
        required_chars: list[str],
    ) -> str:
        """Fill remaining slots, shuffle, and join into the final password."""
        remaining_length = length - len(required_chars)
        remaining_chars = [secrets.choice(allowed_characters) for _ in range(remaining_length)]

        final_password_list = required_chars + remaining_chars
        secrets.SystemRandom().shuffle(final_password_list)
        return "".join(final_password_list)


# Test case
if __name__ == "__main__":
    print("--- Password Generator Test ---")

    # Instance with custom defaults
    pg = PasswordGenerator(length=13, include_symbols=False)

    try:
        password = pg.generate_password()
        print(f"Default instance password : {password}")

        # Override just the length for this one call
        long_password = pg.generate_password(length=20, include_symbols=True)
        print(f"One-off override password : {long_password}")

    except ValueError as e:
        print(f"Error: {e}")
