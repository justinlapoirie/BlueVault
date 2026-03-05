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
        self.minsize(800, 400)  # Prevent window from being too small
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
        # Bind user input events to reset timer
        self.bind_all("<Key>", self.reset_timer_event)
        self.bind_all("<Button>", self.reset_timer_event)

    def reset_timer_event(self, event=None):
        """Reset the auto-logout timer to 5 minutes (300 seconds) on user input."""
        self.time_remaining = self.auto_logout_time
        self.timer_label.config(text=self._format_time(self.time_remaining))

    def create_header(self):
        """Create the header with title, user info, and action buttons."""
        header_frame = tk.Frame(self, bg="#ffffff", height=100, relief=tk.RAISED, borderwidth=1)
        header_frame.pack(fill=tk.X, padx=10, pady=10, expand=False)
        # header_frame.pack_propagate(False)  # Allow header to resize if needed

        # Left side - User info
        left_frame = tk.Frame(header_frame, bg="#ffffff")
        left_frame.pack(side=tk.LEFT, padx=20, pady=10, fill=tk.Y, expand=True)

        tk.Label(
            left_frame,
            text=f"Logged in as: {self.username}",
            font=("Arial", 11),
            bg="#ffffff",
            anchor="w"
        ).pack(anchor="w", fill=tk.X, expand=True)

        # Timer label that will be updated
        self.timer_label = tk.Label(
            left_frame,
            text=self._format_time(self.time_remaining),
            font=("Arial", 11),
            bg="#ffffff",
            anchor="w"
        )
        self.timer_label.pack(anchor="w", pady=(5, 0), fill=tk.X, expand=True)

        # Center - Title
        tk.Label(
            header_frame,
            text="BlueVault",
            font=("Arial", 24, "bold"),
            bg="#ffffff"
        ).pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Right side - Action buttons
        buttons_frame = tk.Frame(header_frame, bg="#ffffff")
        buttons_frame.pack(side=tk.RIGHT, padx=20, pady=10, fill=tk.Y)

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
        button_frame.pack(side=tk.LEFT, padx=8, fill=tk.Y)

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
        btn.pack(fill=tk.X, expand=False)

        # Label under button
        tk.Label(
            button_frame,
            text=label_text,
            font=("Arial", 9),
            bg="#ffffff"
        ).pack(pady=(5, 0), fill=tk.X)

    def create_main_content(self):
        """Create the main content area and store a reference for dynamic updates."""
        self.content_frame = tk.Frame(self, bg="#ffffff", relief=tk.SUNKEN, borderwidth=2)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        # Checkbox to show/hide all passwords
        self.show_passwords_var = tk.BooleanVar(value=False)
        show_pw_checkbox = tk.Checkbutton(
            self.content_frame,
            text="Show Passwords",
            variable=self.show_passwords_var,
            command=self.update_password_visibility,
            bg="#ffffff"
        )
        show_pw_checkbox.pack(anchor="ne", padx=10, pady=(10, 0))
        self.account_widgets = []  # Store references to displayed account widgets
        self.display_placeholder()

    def update_password_visibility(self):
        # Redraw all account widgets to update password visibility
        if self.account_widgets:
            self.display_accounts()

    def display_placeholder(self):
        # Remove all widgets except the show/hide checkbox
        for widget in self.content_frame.winfo_children():
            if not isinstance(widget, tk.Checkbutton):
                widget.destroy()
        tk.Label(
            self.content_frame,
            text="Main Content Area\n(Password entries will appear here)",
            font=("Arial", 14),
            bg="#ffffff",
            fg="#888888"
        ).pack(expand=True, fill=tk.BOTH)

    def add_account_to_content(self, account):
        # Remove placeholder if present
        self.account_widgets.append(account)
        self.display_accounts()

    def display_accounts(self):
        # Remove all widgets except the show/hide checkbox
        for widget in self.content_frame.winfo_children():
            if not isinstance(widget, tk.Checkbutton):
                widget.destroy()
        show_pw = self.show_passwords_var.get()
        for acc in self.account_widgets:
            frame = tk.Frame(self.content_frame, bg="#e3f2fd", relief=tk.RIDGE, borderwidth=1)
            frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(frame, text=f"Website: {acc['website']}", font=("Arial", 12, "bold"), bg="#e3f2fd").pack(anchor="w", padx=10, pady=2)
            tk.Label(frame, text=f"Username: {acc['username']}", font=("Arial", 11), bg="#e3f2fd").pack(anchor="w", padx=10)
            pw_text = acc['password'] if show_pw else '•' * len(acc['password'])
            tk.Label(frame, text=f"Password: {pw_text}", font=("Arial", 11), bg="#e3f2fd").pack(anchor="w", padx=10, pady=(0, 2))
            if acc.get('additional'):
                tk.Label(frame, text=f"Additional: {acc['additional']}", font=("Arial", 10, "italic"), bg="#e3f2fd", fg="#555555").pack(anchor="w", padx=10, pady=(0, 5))

    # ------------------------------------------------------------------
    # Button command methods
    # ------------------------------------------------------------------

    def open_new_account(self):
        """Open a popup to prompt for website, username, and password."""

        popup = tk.Toplevel(self)
        popup.title("Add New Account")
        popup.geometry("400x340")
        popup.minsize(400, 340)
        popup.grab_set()
        # Center the popup on the screen
        popup.update_idletasks()
        w = 400
        h = 340
        ws = popup.winfo_screenwidth()
        hs = popup.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(popup, text="Website:", font=("Arial", 11)).pack(pady=(15, 0))
        website_entry = tk.Entry(popup, width=30, font=("Arial", 11))
        website_entry.pack(pady=(0, 10))

        tk.Label(popup, text="Username:", font=("Arial", 11)).pack()
        username_entry = tk.Entry(popup, width=30, font=("Arial", 11))
        username_entry.pack(pady=(0, 10))


        tk.Label(popup, text="Password:", font=("Arial", 11)).pack()
        password_frame = tk.Frame(popup)
        password_frame.pack(pady=(0, 10))
        password_entry = tk.Entry(password_frame, width=23, font=("Arial", 11))  # visible text
        password_entry.pack(side=tk.LEFT)

        # Password generator button (💡, blue, same as main menu)
        def generate_and_fill_password():
            try:
                from services.password_generator import PasswordGenerator
                # Use default settings or customize as needed
                pg = PasswordGenerator()
                password = pg.generate_password()
                password_entry.delete(0, tk.END)
                password_entry.insert(0, password)
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Failed to generate password: {e}")

        gen_btn = tk.Button(
            password_frame,
            text="💡",
            command=generate_and_fill_password,
            font=("Arial", 13, "bold"),
            bg="#2196F3",
            fg="white",
            activebackground="#2196F3",
            width=3,
            height=1,
            relief=tk.RAISED,
            borderwidth=2
        )

        gen_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Additional info box with placeholder
        tk.Label(popup, text="Additional Info:", font=("Arial", 11)).pack()
        additional_entry = tk.Entry(popup, width=30, font=("Arial", 11), fg="#888888")
        placeholder = "Phone number, 2-Factor-Authentification, etc"
        additional_entry.insert(0, placeholder)

        def on_focus_in(event):
            if additional_entry.get() == placeholder:
                additional_entry.delete(0, tk.END)
                additional_entry.config(fg="#000000")

        def on_focus_out(event):
            if not additional_entry.get():
                additional_entry.insert(0, placeholder)
                additional_entry.config(fg="#888888")

        additional_entry.bind("<FocusIn>", on_focus_in)
        additional_entry.bind("<FocusOut>", on_focus_out)
        additional_entry.pack(pady=(0, 10))


        def submit():
            website = website_entry.get().strip()
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            if not website or not username or not password:
                from tkinter import messagebox
                messagebox.showerror("Error", "All fields are required.")
                return
            account = {"website": website, "username": username, "password": password}
            self.add_account_to_content(account)
            popup.destroy()

        submit_btn = tk.Button(popup, text="Submit", command=submit, font=("Arial", 11), bg="#4CAF50", fg="white")
        submit_btn.pack(pady=(10, 10))

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
