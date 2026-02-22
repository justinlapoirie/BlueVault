import tkinter as tk
import sys
import os

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class MainMenu(tk.Tk):
    def __init__(self, username="User", login_window=None, auto_logout_time=300):
        super().__init__()
        self.title("BlueVault")
        self.geometry("1200x700")
        self.configure(bg="#f0f0f0")
        
        # Store user info and login window reference
        self.username = username
        self.login_window = login_window
        self.auto_logout_time = auto_logout_time  # in seconds
        self.time_remaining = auto_logout_time
        
        # Store reference to opened windows
        self.password_generator_window = None
        self.password_auditor_window = None
        
        self.create_header()
        self.create_main_content()
        
        # Start the auto-logout timer
        self.start_timer()

    def create_header(self):
        """Create the header with title, user info, and action buttons."""
        header_frame = tk.Frame(self, bg="#ffffff", height=100, relief=tk.RAISED, borderwidth=1)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)

        # Left side - User info
        left_frame = tk.Frame(header_frame, bg="#ffffff")
        left_frame.pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            left_frame,
            text=f"Logged in as: {self.username}",
            font=("Arial", 11),
            bg="#ffffff",
            anchor="w"
        ).pack(anchor="w")

        # Timer label that will be updated
        self.timer_label = tk.Label(
            left_frame,
            text=self._format_time(self.time_remaining),
            font=("Arial", 11),
            bg="#ffffff",
            anchor="w"
        )
        self.timer_label.pack(anchor="w", pady=(5, 0))

        # Center - Title
        tk.Label(
            header_frame,
            text="BlueVault",
            font=("Arial", 24, "bold"),
            bg="#ffffff"
        ).pack(side=tk.LEFT, expand=True)

        # Right side - Action buttons
        buttons_frame = tk.Frame(header_frame, bg="#ffffff")
        buttons_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        # Button configuration: (symbol, label, command, color)
        buttons = [
            ("+", "New Account.", self.open_new_account, "#4CAF50"),
            ("💡", "PW Generator", self.open_password_generator, "#2196F3"),
            ("🔍", "PW audit.", self.open_password_auditor, "#FF9800"),
            ("⚙", "Settings.", self.open_settings, "#9E9E9E"),
            ("→", "Log out.", self.logout, "#F44336")
        ]

        for symbol, label_text, command, color in buttons:
            self.create_text_button(buttons_frame, symbol, label_text, command, color)

    def create_text_button(self, parent, symbol, label_text, command, color):
        """Create a text-based button with symbol and label."""
        button_frame = tk.Frame(parent, bg="#ffffff")
        button_frame.pack(side=tk.LEFT, padx=8)

        # Create button with symbol
        btn = tk.Button(
            button_frame,
            text=symbol,
            command=command,
            font=("Arial", 20, "bold"),
            bg=color,
            fg="white",
            activebackground=color,
            cursor="hand2",
            width=3,
            height=1,
            relief=tk.RAISED,
            borderwidth=2
        )
        btn.pack()

        # Label under button
        tk.Label(
            button_frame,
            text=label_text,
            font=("Arial", 9),
            bg="#ffffff"
        ).pack(pady=(5, 0))

    def create_main_content(self):
        """Create the main content area (placeholder for now)."""
        content_frame = tk.Frame(self, bg="#ffffff", relief=tk.SUNKEN, borderwidth=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Placeholder content
        tk.Label(
            content_frame,
            text="Main Content Area\n(Password entries will appear here)",
            font=("Arial", 14),
            bg="#ffffff",
            fg="#888888"
        ).pack(expand=True)

    # ------------------------------------------------------------------
    # Button command methods
    # ------------------------------------------------------------------

    def open_new_account(self):
        """Open new account creation window (placeholder)."""
        print("New Account button clicked - Feature coming soon!")

    def open_password_generator(self):
        """Open the password generator window."""
        # Check if window already exists and is open
        if self.password_generator_window is not None:
            try:
                # Try to raise the existing window
                self.password_generator_window.lift()
                self.password_generator_window.focus_force()
                return
            except tk.TclError:
                # Window was closed, create a new one
                pass

        # Import and create new password generator window
        try:
            from ui_password_generator import PasswordGeneratorApp
            self.password_generator_window = PasswordGeneratorApp()
        except ImportError as e:
            print(f"Error importing password generator: {e}")
            print("Make sure ui_password_generator.py exists in the gui folder")

    def open_password_auditor(self):
        """Open password auditor window."""
        # Check if window already exists and is open
        if self.password_auditor_window is not None:
            try:
                # Try to raise the existing window
                self.password_auditor_window.lift()
                self.password_auditor_window.focus_force()
                return
            except tk.TclError:
                # Window was closed, create a new one
                pass

        # Import and create new password auditor window
        try:
            from ui_password_auditor import PasswordAuditorApp
            self.password_auditor_window = PasswordAuditorApp()
        except ImportError as e:
            print(f"Error importing password auditor: {e}")
            print("Make sure ui_password_auditor.py exists in the gui folder")

    def open_settings(self):
        """Open settings window (placeholder)."""
        print("Settings button clicked - Feature coming soon!")

    def logout(self):
        """Handle logout."""
        if hasattr(self, 'timer_id'):
            self.after_cancel(self.timer_id)  # Stop the timer
        
        # Close any open child windows
        if self.password_generator_window is not None:
            try:
                self.password_generator_window.destroy()
            except:
                pass
        
        if self.password_auditor_window is not None:
            try:
                self.password_auditor_window.destroy()
            except:
                pass
        
        # Destroy main menu
        self.destroy()
        
        # Show login window again if it exists
        if self.login_window is not None:
            self.login_window.deiconify()
            self.login_window.show_initial_screen()

    def start_timer(self):
        """Start the auto-logout countdown timer."""
        self.update_timer()

    def update_timer(self):
        """Update the timer display and handle auto-logout."""
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self.timer_label.config(text=self._format_time(self.time_remaining))
            self.timer_id = self.after(1000, self.update_timer)  # Update every second
        else:
            # Time's up - auto logout
            from tkinter import messagebox
            messagebox.showinfo("Session Expired", "Your session has expired. Please log in again.")
            self.logout()

    def _format_time(self, seconds):
        """Format seconds into a readable time string."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"Time until auto log-out: {minutes}m {secs}s"


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()
