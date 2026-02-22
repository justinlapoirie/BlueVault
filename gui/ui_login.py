import tkinter as tk
from tkinter import messagebox
import sys
import os

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class LoginWindow(tk.Tk):
    """Login window with account creation and login functionality."""
    
    def __init__(self):
        super().__init__()
        self.title("BlueVault - Login")
        self.geometry("600x500")
        self.configure(bg="#f0f0f0")
        
        # Import login manager
        from services.login import LoginManager
        self.login_manager = LoginManager()
        
        # Store the logged-in username (passed to main menu on success)
        self.logged_in_username = None
        
        # Show initial screen
        self.show_initial_screen()

    def clear_window(self):
        """Clear all widgets from the window."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_initial_screen(self):
        """Show the initial screen with LOG IN and CREATE ACCOUNT buttons."""
        self.clear_window()
        
        # Title
        tk.Label(
            self,
            text="BlueVault",
            font=("Arial", 32, "bold"),
            bg="#f0f0f0",
            fg="#2196F3"
        ).pack(pady=50)
        
        tk.Label(
            self,
            text="Secure Password Manager",
            font=("Arial", 14),
            bg="#f0f0f0",
            fg="#666666"
        ).pack(pady=10)
        
        # Buttons frame
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(pady=50)
        
        tk.Button(
            button_frame,
            text="LOG IN",
            command=self.show_login_screen,
            font=("Arial", 14, "bold"),
            bg="#2196F3",
            fg="white",
            width=20,
            height=2,
            cursor="hand2"
        ).pack(pady=10)
        
        tk.Button(
            button_frame,
            text="CREATE ACCOUNT",
            command=self.show_create_account_screen,
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2,
            cursor="hand2"
        ).pack(pady=10)

    def show_login_screen(self):
        """Show the login screen."""
        self.clear_window()
        
        # Title
        tk.Label(
            self,
            text="Login to BlueVault",
            font=("Arial", 24, "bold"),
            bg="#f0f0f0"
        ).pack(pady=30)
        
        # Form frame
        form_frame = tk.Frame(self, bg="#f0f0f0")
        form_frame.pack(pady=20)
        
        # Username
        tk.Label(
            form_frame,
            text="Username:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        
        self.login_username_entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.login_username_entry.grid(row=0, column=1, padx=10, pady=10)
        self.login_username_entry.focus()
        
        # Password
        tk.Label(
            form_frame,
            text="Password:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).grid(row=1, column=0, sticky="e", padx=10, pady=10)
        
        self.login_password_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, show="*")
        self.login_password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Bind Enter key to login
        self.login_username_entry.bind("<Return>", lambda e: self.login_password_entry.focus())
        self.login_password_entry.bind("<Return>", lambda e: self.handle_login())
        
        # Buttons frame
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(pady=30)
        
        tk.Button(
            button_frame,
            text="Login",
            command=self.handle_login,
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            width=12,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Back",
            command=self.show_initial_screen,
            font=("Arial", 12),
            bg="#9E9E9E",
            fg="white",
            width=12,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

    def show_create_account_screen(self):
        """Show the create account screen."""
        self.clear_window()
        
        # Title
        tk.Label(
            self,
            text="Create New Account",
            font=("Arial", 24, "bold"),
            bg="#f0f0f0"
        ).pack(pady=30)
        
        # Form frame
        form_frame = tk.Frame(self, bg="#f0f0f0")
        form_frame.pack(pady=20)
        
        # Username
        tk.Label(
            form_frame,
            text="Username:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        
        self.create_username_entry = tk.Entry(form_frame, font=("Arial", 12), width=25)
        self.create_username_entry.grid(row=0, column=1, padx=10, pady=10)
        self.create_username_entry.focus()
        
        # Password
        tk.Label(
            form_frame,
            text="Password:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).grid(row=1, column=0, sticky="e", padx=10, pady=10)
        
        self.create_password_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, show="*")
        self.create_password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Confirm Password
        tk.Label(
            form_frame,
            text="Confirm Password:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).grid(row=2, column=0, sticky="e", padx=10, pady=10)
        
        self.create_confirm_password_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, show="*")
        self.create_confirm_password_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Bind Enter key navigation
        self.create_username_entry.bind("<Return>", lambda e: self.create_password_entry.focus())
        self.create_password_entry.bind("<Return>", lambda e: self.create_confirm_password_entry.focus())
        self.create_confirm_password_entry.bind("<Return>", lambda e: self.handle_create_account())
        
        # Buttons frame
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(pady=30)
        
        tk.Button(
            button_frame,
            text="Create Account",
            command=self.handle_create_account,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=15,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Back",
            command=self.show_initial_screen,
            font=("Arial", 12),
            bg="#9E9E9E",
            fg="white",
            width=12,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

    def handle_login(self):
        """Handle login button click."""
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get()
        
        # Verify credentials
        success, message = self.login_manager.verify_login(username, password)
        
        if success:
            self.logged_in_username = username
            messagebox.showinfo("Success", f"Welcome back, {username}!")
            self.open_main_menu()
        else:
            messagebox.showerror("Login Failed", message)
            self.login_password_entry.delete(0, tk.END)
            self.login_password_entry.focus()

    def handle_create_account(self):
        """Handle create account button click."""
        username = self.create_username_entry.get().strip()
        password = self.create_password_entry.get()
        confirm_password = self.create_confirm_password_entry.get()
        
        # Check if passwords match
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            self.create_password_entry.delete(0, tk.END)
            self.create_confirm_password_entry.delete(0, tk.END)
            self.create_password_entry.focus()
            return
        
        # Attempt to create account
        success, message = self.login_manager.create_account(username, password)
        
        if success:
            messagebox.showinfo("Success", "Account created. Please log in.")
            self.show_initial_screen()
        else:
            messagebox.showerror("Error", message)

    def open_main_menu(self):
        """Close login window and open main menu."""
        # Import here to avoid circular import
        from ui_main_menu import MainMenu
        
        # Get auto-logout time from config if available
        try:
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            from BlueVaultMain import AppConfig
            auto_logout_time = AppConfig.AUTO_LOGOUT_TIME
            AppConfig.CURRENT_USER = self.logged_in_username
        except ImportError:
            # Fallback if BlueVaultMain not found
            auto_logout_time = 300  # 5 minutes default
        
        # Hide login window
        self.withdraw()
        
        # Open main menu with username and auto-logout time
        main_menu = MainMenu(
            username=self.logged_in_username, 
            login_window=self, 
            auto_logout_time=auto_logout_time
        )
        
        # If main menu is closed, show login again
        # (This is handled in main menu's logout function)


# For standalone testing
if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
