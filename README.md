# BlueVault
Locally Encrypted Password Generation and Management Desktop Application

CS370 Collaborative Project IN DEVELOPMENT by GROUP 4: Justin Lapoirie, Ethan Esparza, Cooper Frank

## Current Features:
- Login/Logout feature with secure account info storage and proper error handling
- main menu with clean GUI
- Account management system that allows users to store account information to various applications
- Auto time-out feature(default 5 minutes, eventually will be customizable with settings button)
- Password Generator with customizable parameters and copy-to-clipboard functionality
- Password Auditor that checks strength of password and compares it to known breaches

## In Development:
- settings that allow user to customize global variables, password strength requirements, etc
- Email incorporation for 2FA, account recovery, verification, etc
- import/export user data "vault" as encrpyted zip file
  
## Future Features:
- global encryption/decryption for improved security
- session security, auto-logout on sleep, shutdown, etc
- account search bar to search through account modules
- audit log showing recent changes
- .EXE desktop application implementation

## File Structure:
<pre>
    BlueVault/
    ├── BlueVaultMain.py              # Main application entry point (RUN THIS)
    ├── gui/
    │   ├── ui_login.py               # Master login and account creation GUI
    │   ├── ui_main_menu.py           # Main menu interface
    │   └── ui_password_generator.py  # Password generator window
    |   └── ui_password_auditor.py    # Password auditor window
    |   └── ui_settings.py            # Controls global variables of BlueVaultMain.py + import/export Vault functionality
    |   └── ui_account.py             # Store username, password, notes, and hyperlink for external applications
    ├── services/
    │   ├── login.py                  # Authentication backend
    │   └── password_generator.py     # Password generation class
    │   └── password_auditor.py       # Analyzes strength of password + compares to breaches
    │   └── account.py                # Account module backend responsible for vault management
    ├── user_data/                    # Created automatically
    |   └── accounts.json             # Encrypted master accounts (auto-generated)
    │   └── vault_(user).json         # Encrypted username/password data for account modules, lock/unlock with associated master user
    ├── utils/
    │   └── common_passwords.txt      # Common passwords based on rockyou breach
</pre>


