import secrets 
import string

def generate_password(length = 12, include_uppercase = True, include_lowercase = True, include_digits = True, include_symbols = True):
    # Dictionary of char sets
    char_sets = {
        'uppercase': string.ascii_uppercase,
        'lowercase': string.ascii_lowercase,
        'digits': string.digits,
        'symbols': string.punctuation
    }

    # Minimum password length check
    if length < 7:
        raise ValueError("Password length must be at least 7 characters.")
    
    # Building the pool of possible characters based on parameters
    allowed_characters = "" # holds all allowed characters based on user choices
    required_chars = [] # holds at least one character from each selected category for minimum requirements
    
    if include_uppercase:
        allowed_characters += char_sets['uppercase']
        required_chars.append(secrets.choice(char_sets['uppercase']))
    if include_lowercase:
        allowed_characters += char_sets['lowercase']
        required_chars.append(secrets.choice(char_sets['lowercase']))
    if include_digits:
        allowed_characters += char_sets['digits']
        required_chars.append(secrets.choice(char_sets['digits']))
    if include_symbols:
        allowed_characters += char_sets['symbols']
        required_chars.append(secrets.choice(char_sets['symbols']))

    if not allowed_characters: # error if no character types are selected
        raise ValueError("At least one character type must be included.")
    if length < len(required_chars): # won't happen with 7 character minimum, but just in case
        raise ValueError(f"Password length must be at least {len(required_chars)} characters to include all selected character types.")
    
     # calculate how many more characters we need to fill the password, and generate them randomly from the allowed set
    remaining_length = length - len(required_chars)
    remaining_chars = [secrets.choice(allowed_characters) for _ in range(remaining_length)]

    # Combine required characters with the remaining random characters and shuffle
    final_password_list = required_chars + remaining_chars
    secrets.SystemRandom().shuffle(final_password_list)
    return ''.join(final_password_list)

# Code to test the function
# if __name__ == "__main__":
#     print("--- Password Generator Test ---")
#     try:
#         password = generate_password(length=13, include_uppercase=True, include_lowercase=True, include_digits=True, include_symbols=False)
#         print(f"Generated Password: {password}")
#     except ValueError as e:
#         print(f"Error: {e}")
