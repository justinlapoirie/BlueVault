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
        self.geometry("500x400")
        self.configure(bg="#23272a")  # Dark gray background

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
        """Show the initial screen with LOG IN and CREATE ACCOUNT buttons and logo."""
        self.clear_window()

        # Center frame for all content
        center_frame = tk.Frame(self, bg="#23272a")
        center_frame.pack(expand=True)

        # Logo (place logo.png in gui/)
        try:
            from tkinter import PhotoImage
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                self.logo_img = PhotoImage(file=logo_path)
                logo_label = tk.Label(center_frame, image=self.logo_img, bg="#23272a")
                logo_label.pack(pady=(20, 10))
            else:
                tk.Label(center_frame, text="", bg="#23272a").pack(pady=(20, 10))
        except Exception:
            tk.Label(center_frame, text="", bg="#23272a").pack(pady=(20, 10))

        # Button style
        button_style = {
            "font": ("Arial", 14, "bold"),
            "width": 20,
            "bg": "#2196F3",
            "fg": "white",
            "activebackground": "#1976D2",
            "activeforeground": "#ffffff",
            "cursor": "hand2",
            "highlightbackground": "#23272a",
            "highlightthickness": 0,
            "bd": 0,
            "relief": tk.FLAT,
            "padx": 0,
            "pady": 0
        }

        login_btn = tk.Button(center_frame, text="LOG IN", command=self.show_login_screen, **button_style)
        login_btn.pack(pady=(10, 10), ipady=6, ipadx=6)

        create_btn = tk.Button(center_frame, text="CREATE ACCOUNT", command=self.show_create_account_screen, **button_style)
        create_btn.pack(pady=(0, 10), ipady=6, ipadx=6)

    def show_login_screen(self):
        """Show the login screen."""
        self.clear_window()

        # Center frame for all content
        center_frame = tk.Frame(self, bg="#23272a")
        center_frame.pack(expand=True)

        # Form frame with border for focus
        form_frame = tk.Frame(center_frame, bg="#23272a", highlightbackground="#7289da", highlightthickness=2, bd=0)
        form_frame.pack(pady=30, padx=20)

        # Title
        tk.Label(
            form_frame,
            text="Login to BlueVault",
            font=("Arial", 20, "bold"),
            bg="#23272a",
            fg="#7289da"
        ).grid(row=0, column=0, columnspan=2, pady=(10, 20))

        # Username
        tk.Label(
            form_frame,
            text="Username:",
            font=("Arial", 12),
            bg="#23272a",
            fg="#ffffff"
        ).grid(row=1, column=0, sticky="e", padx=10, pady=10)

        self.login_username_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, bg="#2c2f33", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground="#444")
        self.login_username_entry.grid(row=1, column=1, padx=10, pady=10)
        self.login_username_entry.focus()

        # Password
        tk.Label(
            form_frame,
            text="Password:",
            font=("Arial", 12),
            bg="#23272a",
            fg="#ffffff"
        ).grid(row=2, column=0, sticky="e", padx=10, pady=10)

        self.login_password_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, show="*", bg="#2c2f33", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground="#444")
        self.login_password_entry.grid(row=2, column=1, padx=10, pady=10)

        # Bind Enter key to login
        self.login_username_entry.bind("<Return>", lambda e: self.login_password_entry.focus())
        self.login_password_entry.bind("<Return>", lambda e: self.handle_login())

        # Button style
        button_style = {
            "font": ("Arial", 13, "bold"),
            "width": 15,
            "bg": "#2196F3",
            "fg": "white",
            "activebackground": "#1976D2",
            "activeforeground": "#ffffff",
            "cursor": "hand2",
            "highlightbackground": "#23272a",
            "highlightthickness": 0,
            "bd": 0,
            "relief": tk.FLAT,
            "padx": 0,
            "pady": 0
        }

        # Buttons frame
        button_frame = tk.Frame(form_frame, bg="#23272a")
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 10))

        login_btn = tk.Button(button_frame, text="Log In", command=self.handle_login, **button_style)
        login_btn.pack(side=tk.LEFT, padx=8, ipady=4, ipadx=4)

        back_btn = tk.Button(button_frame, text="Back", command=self.show_initial_screen, **button_style)
        back_btn.pack(side=tk.LEFT, padx=8, ipady=4, ipadx=4)

    def show_create_account_screen(self):
        """Show the create account screen."""
        self.clear_window()

        # Center frame for all content
        center_frame = tk.Frame(self, bg="#23272a")
        center_frame.pack(expand=True)

        # Form frame with border for focus
        form_frame = tk.Frame(center_frame, bg="#23272a", highlightbackground="#7289da", highlightthickness=2, bd=0)
        form_frame.pack(pady=30, padx=20)

        # Title
        tk.Label(
            form_frame,
            text="Create New Account",
            font=("Arial", 20, "bold"),
            bg="#23272a",
            fg="#7289da"
        ).grid(row=0, column=0, columnspan=2, pady=(10, 20))

        # Username
        tk.Label(
            form_frame,
            text="Username:",
            font=("Arial", 12),
            bg="#23272a",
            fg="#ffffff"
        ).grid(row=1, column=0, sticky="e", padx=10, pady=10)

        self.create_username_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, bg="#2c2f33", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground="#444")
        self.create_username_entry.grid(row=1, column=1, padx=10, pady=10)
        self.create_username_entry.focus()

        # Email
        tk.Label(
            form_frame,
            text="Email:",
            font=("Arial", 12),
            bg="#23272a",
            fg="#ffffff"
        ).grid(row=2, column=0, sticky="e", padx=10, pady=10)

        self.create_email_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, bg="#2c2f33", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground="#444")
        self.create_email_entry.grid(row=2, column=1, padx=10, pady=10)

        # Password
        tk.Label(
            form_frame,
            text="Password:",
            font=("Arial", 12),
            bg="#23272a",
            fg="#ffffff"
        ).grid(row=3, column=0, sticky="e", padx=10, pady=10)

        self.create_password_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, show="*", bg="#2c2f33", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground="#444")
        self.create_password_entry.grid(row=3, column=1, padx=10, pady=10)

        # Confirm Password
        tk.Label(
            form_frame,
            text="Confirm Password:",
            font=("Arial", 12),
            bg="#23272a",
            fg="#ffffff"
        ).grid(row=4, column=0, sticky="e", padx=10, pady=10)

        self.create_confirm_password_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, show="*", bg="#2c2f33", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground="#444")
        self.create_confirm_password_entry.grid(row=4, column=1, padx=10, pady=10)

        # Bind Enter key navigation
        self.create_username_entry.bind("<Return>", lambda e: self.create_email_entry.focus())
        self.create_email_entry.bind("<Return>", lambda e: self.create_password_entry.focus())
        self.create_password_entry.bind("<Return>", lambda e: self.create_confirm_password_entry.focus())
        self.create_confirm_password_entry.bind("<Return>", lambda e: self.handle_create_account())

        # Button style
        button_style = {
            "font": ("Arial", 13, "bold"),
            "width": 15,
            "bg": "#2196F3",
            "fg": "white",
            "activebackground": "#1976D2",
            "activeforeground": "#ffffff",
            "cursor": "hand2",
            "highlightbackground": "#23272a",
            "highlightthickness": 0,
            "bd": 0,
            "relief": tk.FLAT,
            "padx": 0,
            "pady": 0
        }

        # Buttons frame
        button_frame = tk.Frame(form_frame, bg="#23272a")
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 10))

        create_btn = tk.Button(button_frame, text="Create Account", command=self.handle_create_account, **button_style)
        create_btn.pack(side=tk.LEFT, padx=8, ipady=4, ipadx=4)

        back_btn = tk.Button(button_frame, text="Back", command=self.show_initial_screen, **button_style)
        back_btn.pack(side=tk.LEFT, padx=8, ipady=4, ipadx=4)

    def handle_login(self):
        """Handle login button click."""
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get()

        # Verify credentials
        success, message = self.login_manager.verify_login(username, password)

        if success:
            self.logged_in_username = username
            self.master_password = password  # Store for encryption key
            messagebox.showinfo("Success", f"Welcome back, {username}!")
            self.open_main_menu()
        else:
            messagebox.showerror("Login Failed", message)
            self.login_password_entry.delete(0, tk.END)
            self.login_password_entry.focus()

    def handle_create_account(self):
        """Handle create account button click."""
        username = self.create_username_entry.get().strip()
        email = self.create_email_entry.get().strip()
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
        success, message = self.login_manager.create_account(username, password, email)

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

        # Open main menu with username, auto-logout time, and master password
        main_menu = MainMenu(
            username=self.logged_in_username,
            login_window=self,
            auto_logout_time=auto_logout_time,
            master_password=self.master_password
        )

        # If main menu is closed, show login again
        # (This is handled in main menu's logout function)


# For standalone testing
if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()