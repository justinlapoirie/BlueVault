# BlueVault
Locally Encrypted Password Generation and Management Desktop Application

CS370 Collaborative Project by GROUP 4: Justin Lapoirie, Ethan Esparza, Cooper Frank

Current Features:
- Login/Logout feature with secure account info storage and proper error handling
- main menu with clean GUI
- Auto time-out feature(default 5 minutes, eventually will be customizable with settings button)
- Password Generator with customizable parameters and copy-to-clipboard functionality

In Progress:
- Password Auditor that checks strength of password and compares it to known breaches
- settings that allow user to customize global variables, password strength requirements, etc
- Account management system that allows users to store account information to various applications
- global encryption/decryption to make more secure
- import/export user data "vault" as encrpyted zip file

File Structure:
BlueVault/
├── BlueVaultMain.py              # Main application entry point (RUN THIS)
├── gui/
│   ├── ui_login.py               # Login and account creation GUI
│   ├── ui_main_menu.py           # Main menu interface
│   └── ui_password_generator.py  # Password generator window
|   └── ui_settings.py            # Controls global variables of BlueVaultMain.py + import/export Vault functionality
├── services/
│   ├── login.py                  # Authentication backend
│   └── password_generator.py     # Password generation class
│   └── password_auditor.py       # analyzes strength of password + compares to breaches
├── user_data/                    # Created automatically
    └── accounts.json             # Encrypted user accounts (auto-generated)
├── utils/
│   ├── rockyou.txt               # common password list
│   └── other

