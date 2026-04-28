# BlueVault
Locally Encrypted Password Generation and Management Desktop Application

CS370 Collaborative Project IN DEVELOPMENT by GROUP 4: Justin Lapoirie, Ethan Esparza, Cooper Frank

## Current Features:
- Login/Logout feature with secure account info storage and proper error handling
- main menu with clean GUI
- Account management system that allows users to store account information to various applications
- Settings manager that allows users to customize security features, password requirements and reminders, etc
- Password Generator with customizable parameters and copy-to-clipboard functionality
- Password Auditor that checks strength of password and compares it to known breaches
- import/export user data "vault" as encrpyted zip file

## In Development (By Priority):
- UI overhaul
- .EXE desktop application implementation
- Session security, auto-logout on sleep, shutdown, etc
- Audit log showing recent changes
- Email incorporation for 2FA, account recovery, verification, etc

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
    │   └── settings_(user).json      # stores settings information for user. Basic formatting - no need for encryption
    ├── utils/
    │   └── common_passwords.txt      # Common passwords based on rockyou breach
    │   └── entropy_calculator.py     # Entropy calculation used in account creationn and password auditor
</pre>


