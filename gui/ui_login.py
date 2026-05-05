import tkinter as tk
from tkinter import messagebox
import sys
import os

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui_controller import theme


class LoginWindow(tk.Tk):
    """Login window with account creation and login functionality."""

    def __init__(self):
        super().__init__()
        self.title("BlueVault - Login")
        self.geometry("500x500")
        self.configure(bg=theme["app_bg"])
        theme.configure_ttk(self)

        # Import login manager
        from services.login import LoginManager
        self.login_manager = LoginManager()

        # Store the logged-in username (passed to main menu on success)
        self.logged_in_username = None

        # Track which screen is currently showing so theme changes can
        # rebuild it without losing context.
        self._current_screen = "initial"

        # Show initial screen
        self.show_initial_screen()

        # Subscribe to theme changes so the (rare) live toggle still
        # repaints the login screen.
        theme.subscribe(self._apply_theme)
        self.bind("<Destroy>", self._on_destroy, add="+")

        # Clicking X must end the process cleanly.
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _on_window_close(self):
        """Clean shutdown when the login screen's X button is clicked."""
        try:
            theme.unsubscribe(self._apply_theme)
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Theme integration
    # ------------------------------------------------------------------
    def _apply_theme(self):
        try:
            self.configure(bg=theme["app_bg"])
            theme.configure_ttk(self)
            screen = getattr(self, "_current_screen", "initial")
            if screen == "login":
                self.show_login_screen()
            elif screen == "create":
                self.show_create_account_screen()
            else:
                self.show_initial_screen()
        except tk.TclError:
            pass

    def _on_destroy(self, event):
        if event.widget is self:
            theme.unsubscribe(self._apply_theme)

    def clear_window(self):
        """Clear all widgets from the window."""
        for widget in self.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------
    def show_initial_screen(self):
        """Show the initial screen with LOG IN and CREATE ACCOUNT buttons and logo."""
        self._current_screen = "initial"
        self.clear_window()
        self.configure(bg=theme["app_bg"])

        center_frame = tk.Frame(self, bg=theme["app_bg"])
        center_frame.pack(expand=True)

        # Logo
        try:
            from tkinter import PhotoImage
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                self.logo_img = PhotoImage(file=logo_path)
                tk.Label(center_frame, image=self.logo_img,
                         bg=theme["app_bg"]).pack(pady=(20, 6))
            else:
                tk.Label(center_frame, text="", bg=theme["app_bg"]).pack(pady=(20, 6))
        except Exception:
            tk.Label(center_frame, text="", bg=theme["app_bg"]).pack(pady=(20, 6))

        tk.Label(
            center_frame,
            text="BlueVault",
            font=("Segoe UI", 22, "bold"),
            bg=theme["app_bg"],
            fg=theme["accent"],
        ).pack()

        tk.Label(
            center_frame,
            text="Your secure password manager",
            font=("Segoe UI", 10),
            bg=theme["app_bg"],
            fg=theme["text_muted"],
        ).pack(pady=(2, 24))

        btn_style = self._initial_button_style()

        login_btn = tk.Button(
            center_frame, text="Log In",
            command=self.show_login_screen, **btn_style
        )
        login_btn.pack(pady=(0, 10), ipady=8, ipadx=10)

        create_btn = tk.Button(
            center_frame, text="Create Account",
            command=self.show_create_account_screen, **btn_style
        )
        create_btn.pack(ipady=8, ipadx=10)

    def show_login_screen(self):
        """Show the login screen."""
        self._current_screen = "login"
        self.clear_window()
        self.configure(bg=theme["app_bg"])

        center_frame = tk.Frame(self, bg=theme["app_bg"])
        center_frame.pack(expand=True)

        # Card panel
        card = tk.Frame(
            center_frame,
            bg=theme["surface_bg"],
            highlightbackground=theme["section_border"],
            highlightthickness=1,
            bd=0,
        )
        card.pack(pady=20, padx=30, ipadx=20, ipady=20)

        tk.Label(
            card,
            text="Welcome Back",
            font=("Segoe UI", 20, "bold"),
            bg=theme["surface_bg"],
            fg=theme["accent"],
        ).grid(row=0, column=0, columnspan=2, pady=(20, 4))

        tk.Label(
            card,
            text="Sign in to your vault",
            font=("Segoe UI", 10),
            bg=theme["surface_bg"],
            fg=theme["text_muted"],
        ).grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Username
        tk.Label(
            card,
            text="Username",
            font=("Segoe UI", 10, "bold"),
            bg=theme["surface_bg"],
            fg=theme["text_secondary"],
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 4))

        self.login_username_entry = tk.Entry(
            card, font=("Segoe UI", 12), width=26, **theme.entry_style()
        )
        self.login_username_entry.grid(row=3, column=0, columnspan=2,
                                       padx=14, pady=(0, 14), sticky="ew")
        self.login_username_entry.focus()

        # Password
        tk.Label(
            card,
            text="Master Password",
            font=("Segoe UI", 10, "bold"),
            bg=theme["surface_bg"],
            fg=theme["text_secondary"],
        ).grid(row=4, column=0, sticky="w", padx=14, pady=(0, 4))

        self.login_password_entry = tk.Entry(
            card, font=("Segoe UI", 12), width=26, show="*", **theme.entry_style()
        )
        self.login_password_entry.grid(row=5, column=0, columnspan=2,
                                       padx=14, pady=(0, 20), sticky="ew")

        self.login_username_entry.bind("<Return>",
                                       lambda e: self.login_password_entry.focus())
        self.login_password_entry.bind("<Return>", lambda e: self.handle_login())

        # Buttons (right-aligned)
        btn_row = tk.Frame(card, bg=theme["surface_bg"])
        btn_row.grid(row=6, column=0, columnspan=2,
                     padx=14, pady=(0, 20), sticky="e")

        back_style = theme.secondary_button_style()
        back_style.update(font=("Segoe UI", 10), padx=14, pady=6)
        tk.Button(btn_row, text="Back",
                  command=self.show_initial_screen, **back_style).pack(
            side=tk.LEFT, padx=(0, 8))

        login_style = theme.primary_button_style()
        login_style.update(font=("Segoe UI", 10, "bold"), padx=14, pady=6)
        tk.Button(btn_row, text="Log In",
                  command=self.handle_login, **login_style).pack(side=tk.LEFT)

    def show_create_account_screen(self):
        """Show the create account screen."""
        self._current_screen = "create"
        self.clear_window()
        self.configure(bg=theme["app_bg"])

        center_frame = tk.Frame(self, bg=theme["app_bg"])
        center_frame.pack(expand=True)

        card = tk.Frame(
            center_frame,
            bg=theme["surface_bg"],
            highlightbackground=theme["section_border"],
            highlightthickness=1,
            bd=0,
        )
        card.pack(pady=20, padx=30, ipadx=20, ipady=10)

        tk.Label(
            card,
            text="Create Account",
            font=("Segoe UI", 20, "bold"),
            bg=theme["surface_bg"],
            fg=theme["accent"],
        ).grid(row=0, column=0, columnspan=2, pady=(20, 18))

        fields = [
            ("Username",         "create_username_entry",        False),
            ("Email",            "create_email_entry",           False),
            ("Master Password",  "create_password_entry",        True),
            ("Confirm Password", "create_confirm_password_entry", True),
        ]
        for r, (label_text, attr, hide) in enumerate(fields, start=1):
            tk.Label(
                card,
                text=label_text,
                font=("Segoe UI", 10, "bold"),
                bg=theme["surface_bg"],
                fg=theme["text_secondary"],
            ).grid(row=(r - 1) * 2 + 1, column=0, sticky="w",
                   padx=14, pady=(0, 4))

            entry_kwargs = dict(theme.entry_style())
            entry_kwargs.update(font=("Segoe UI", 11), width=26)
            if hide:
                entry_kwargs["show"] = "*"
            entry = tk.Entry(card, **entry_kwargs)
            entry.grid(row=(r - 1) * 2 + 2, column=0, columnspan=2,
                       padx=14, pady=(0, 14), sticky="ew")
            setattr(self, attr, entry)

        self.create_username_entry.focus()
        self.create_username_entry.bind("<Return>",
            lambda e: self.create_email_entry.focus())
        self.create_email_entry.bind("<Return>",
            lambda e: self.create_password_entry.focus())
        self.create_password_entry.bind("<Return>",
            lambda e: self.create_confirm_password_entry.focus())
        self.create_confirm_password_entry.bind("<Return>",
            lambda e: self.handle_create_account())

        btn_row = tk.Frame(card, bg=theme["surface_bg"])
        btn_row.grid(row=9, column=0, columnspan=2,
                     padx=14, pady=(0, 20), sticky="e")

        back_style = theme.secondary_button_style()
        back_style.update(font=("Segoe UI", 10), padx=14, pady=6)
        tk.Button(btn_row, text="Back",
                  command=self.show_initial_screen, **back_style).pack(
            side=tk.LEFT, padx=(0, 8))

        create_style = theme.primary_button_style()
        create_style.update(font=("Segoe UI", 10, "bold"), padx=14, pady=6)
        tk.Button(btn_row, text="Create Account",
                  command=self.handle_create_account, **create_style).pack(
            side=tk.LEFT)

    # ------------------------------------------------------------------
    # Button style helpers
    # ------------------------------------------------------------------
    def _initial_button_style(self) -> dict:
        return {
            "font": ("Segoe UI", 13, "bold"),
            "width": 20,
            "bg": theme["btn_primary_bg"],
            "fg": theme["btn_primary_fg"],
            "activebackground": theme["btn_primary_active"],
            "activeforeground": theme["btn_primary_fg"],
            "cursor": "hand2",
            "highlightbackground": theme["app_bg"],
            "highlightthickness": 0,
            "bd": 0,
            "relief": tk.FLAT,
            "padx": 0,
            "pady": 0,
        }

    def _form_button_style(self) -> dict:
        style = self._initial_button_style()
        style["font"] = ("Segoe UI", 12, "bold")
        style["width"] = 15
        return style

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def handle_login(self):
        """Handle login button click."""
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get()

        success, message = self.login_manager.verify_login(username, password)

        if success:
            self.logged_in_username = username
            self.master_password = password
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
            master_password=self.master_password,
        )

        # If main menu is closed, show login again
        # (handled in main menu's logout function)


# For standalone testing
if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
