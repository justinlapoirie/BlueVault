"""
BlueVault Main Application Controller

This file manages the application flow and global settings.
Run this file to start the BlueVault application.
"""

import sys
import os

# Ensure the gui directory is in sys.path
gui_dir = os.path.join(os.path.dirname(__file__), "gui")
sys.path.append(gui_dir)

# Global application settings
class AppConfig:
    """Global configuration for BlueVault application."""
    
    # Auto-logout timer (in seconds)
    # Default: 300 seconds (5 minutes)
    # Eventually customizable in settings.py
    AUTO_LOGOUT_TIME = 300
    
    # Application version
    VERSION = "1.0.0"
    
    # Application name
    APP_NAME = "BlueVault"
    
    # Current logged-in user (set during login)
    CURRENT_USER = None


def main():
    """Main entry point for BlueVault application."""
    print(f"Starting {AppConfig.APP_NAME} v{AppConfig.VERSION}...")
    
    # Import login window
    from gui.ui_login import LoginWindow
    
    # Start with login window
    app = LoginWindow()
    app.mainloop()
    
    print("BlueVault closed.")


if __name__ == "__main__":
    main()
