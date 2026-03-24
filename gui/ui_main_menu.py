import tkinter as tk
import sys
import os

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class MainMenu(tk.Tk):
    def __init__(self, username="User", login_window=None, auto_logout_time=300, master_password=None):
        super().__init__()
        self.title("BlueVault")
        self.geometry("1100x700")
        self.configure(bg="#f0f0f0")

        # Store user info and login window reference
        self.username = username
        self.login_window = login_window
        self.auto_logout_time = auto_logout_time  # in seconds
        self.time_remaining = auto_logout_time

        # Initialize account manager
        from services.account import AccountManager
        self.account_manager = AccountManager(username, master_password)

        # Store reference to opened windows
        self.password_generator_window = None
        self.password_auditor_window = None

        self.create_header()
        self.create_main_content()

        # Bind window resize to refresh grid layout
        self.bind("<Configure>", self._on_window_resize)
        self._resize_timer = None

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
        """Create the main content area with account cards."""
        # Main content frame
        content_frame = tk.Frame(self, bg="#ffffff", relief=tk.SUNKEN, borderwidth=2)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create canvas for scrolling
        self.canvas = tk.Canvas(content_frame, bg="#ffffff", highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)

        # Scrollable frame
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ffffff")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Load and display accounts
        self.refresh_accounts()

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def refresh_accounts(self):
        """Load accounts and refresh the display."""
        # Clear existing account cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Load accounts from manager
        accounts = self.account_manager.get_all_accounts()

        if not accounts:
            # Show empty state message
            tk.Label(
                self.scrollable_frame,
                text="No accounts yet.\n\nClick the '+' button to create your first account!",
                font=("Arial", 14),
                bg="#ffffff",
                fg="#888888"
            ).grid(row=0, column=0, pady=100, padx=100)
        else:
            # Calculate number of columns based on window width
            # Each card needs approximately 400 pixels width
            window_width = self.winfo_width()
            if window_width < 100:  # Window not yet sized
                window_width = 1200  # Use default

            # Account for scrollbar and padding
            available_width = window_width - 60
            card_width = 400
            num_columns = max(1, available_width // card_width)

            # Display accounts in grid
            for index, account in enumerate(accounts):
                row = index // num_columns
                col = index % num_columns
                self.create_account_card(account, row, col)

            # Configure grid columns to expand evenly
            for col in range(num_columns):
                self.scrollable_frame.grid_columnconfigure(col, weight=1, uniform="column")

    def create_account_card(self, account, row, col):
        """Create a card widget for an account entry."""
        from datetime import datetime

        # Card frame - use grid instead of pack
        card = tk.Frame(
            self.scrollable_frame,
            bg="#f9f9f9",
            relief=tk.RAISED,
            borderwidth=1
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Top row: Account name and action buttons
        top_frame = tk.Frame(card, bg="#f9f9f9")
        top_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        # Account name
        tk.Label(
            top_frame,
            text=account["account_name"],
            font=("Arial", 14, "bold"),
            bg="#f9f9f9",
            fg="#2196F3"
        ).pack(side=tk.LEFT)

        # Action buttons frame (right side)
        action_frame = tk.Frame(top_frame, bg="#f9f9f9")
        action_frame.pack(side=tk.RIGHT)

        # Edit button (pencil)
        edit_btn = tk.Button(
            action_frame,
            text="✏",
            command=lambda: self.edit_account(account["id"]),
            font=("Arial", 14),
            bg="#f9f9f9",
            fg="#2196F3",
            relief=tk.FLAT,
            cursor="hand2",
            width=2
        )
        edit_btn.pack(side=tk.LEFT, padx=5)

        # Delete button (trash)
        delete_btn = tk.Button(
            action_frame,
            text="🗑",
            command=lambda: self.delete_account(account["id"]),
            font=("Arial", 14),
            bg="#f9f9f9",
            fg="#F44336",
            relief=tk.FLAT,
            cursor="hand2",
            width=2
        )
        delete_btn.pack(side=tk.LEFT, padx=5)

        # Content frame
        content_frame = tk.Frame(card, bg="#f9f9f9")
        content_frame.pack(fill=tk.X, padx=15, pady=5)

        # Username row
        username_frame = tk.Frame(content_frame, bg="#f9f9f9")
        username_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            username_frame,
            text="Username:",
            font=("Arial", 10, "bold"),
            bg="#f9f9f9",
            width=12,
            anchor="w"
        ).pack(side=tk.LEFT)

        username_display = tk.Entry(
            username_frame,
            font=("Arial", 10),
            bg="#ffffff",
            relief=tk.FLAT,
            state="readonly",
            width=40
        )
        username_display.pack(side=tk.LEFT, padx=5)
        username_display.configure(state="normal")
        username_display.insert(0, account["username"])
        username_display.configure(state="readonly")

        # Copy username button
        tk.Button(
            username_frame,
            text="📋",
            command=lambda: self.copy_to_clipboard(account["username"], "Username"),
            font=("Arial", 10),
            bg="#f9f9f9",
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT)

        # Password row
        password_frame = tk.Frame(content_frame, bg="#f9f9f9")
        password_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            password_frame,
            text="Password:",
            font=("Arial", 10, "bold"),
            bg="#f9f9f9",
            width=12,
            anchor="w"
        ).pack(side=tk.LEFT)

        password_var = tk.StringVar(value="*" * 10)
        password_display = tk.Entry(
            password_frame,
            textvariable=password_var,
            font=("Arial", 10),
            bg="#ffffff",
            relief=tk.FLAT,
            state="readonly",
            width=40
        )
        password_display.pack(side=tk.LEFT, padx=5)

        # Toggle password visibility
        show_password = [False]  # Use list to maintain state in closure

        def toggle_password_visibility():
            if show_password[0]:
                password_var.set("*" * 10)
                show_btn.config(text="👁")
                show_password[0] = False
            else:
                password_var.set(account["password"])
                show_btn.config(text="👁‍🗨")
                show_password[0] = True
            # Force display update
            password_display.update_idletasks()

        # Show/hide password button (eye)
        show_btn = tk.Button(
            password_frame,
            text="👁",
            command=toggle_password_visibility,
            font=("Arial", 10),
            bg="#f9f9f9",
            relief=tk.FLAT,
            cursor="hand2"
        )
        show_btn.pack(side=tk.LEFT)

        # Copy password button
        tk.Button(
            password_frame,
            text="📋",
            command=lambda: self.copy_to_clipboard(account["password"], "Password"),
            font=("Arial", 10),
            bg="#f9f9f9",
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT)

        # Website URL (if present)
        if account.get("website_url"):
            website_frame = tk.Frame(content_frame, bg="#f9f9f9")
            website_frame.pack(fill=tk.X, pady=5)

            tk.Label(
                website_frame,
                text="Website:",
                font=("Arial", 10, "bold"),
                bg="#f9f9f9",
                width=12,
                anchor="w"
            ).pack(side=tk.LEFT)

            website_label = tk.Label(
                website_frame,
                text=account["website_url"],
                font=("Arial", 10, "underline"),
                bg="#f9f9f9",
                fg="#2196F3",
                cursor="hand2"
            )
            website_label.pack(side=tk.LEFT, padx=5)
            website_label.bind("<Button-1>", lambda e: self.open_website(account["website_url"]))

        # Notes (if present)
        if account.get("notes"):
            notes_frame = tk.Frame(content_frame, bg="#f9f9f9")
            notes_frame.pack(fill=tk.X, pady=5)

            tk.Label(
                notes_frame,
                text="Notes:",
                font=("Arial", 10, "bold"),
                bg="#f9f9f9",
                width=12,
                anchor="w"
            ).pack(side=tk.LEFT, anchor="n")

            notes_text = tk.Text(
                notes_frame,
                font=("Arial", 9),
                bg="#ffffff",
                height=3,
                width=40,
                wrap=tk.WORD,
                state="normal"
            )
            notes_text.pack(side=tk.LEFT, padx=5)
            notes_text.insert(1.0, account["notes"])
            notes_text.config(state="disabled")

        # Bottom info row
        info_frame = tk.Frame(card, bg="#f9f9f9")
        info_frame.pack(fill=tk.X, padx=15, pady=(5, 10))

        # Calculate password age
        last_change = datetime.fromisoformat(account["last_password_change"])
        now = datetime.now()
        delta = now - last_change

        # Format time ago
        if delta.days == 0:
            time_ago = "Today"
        elif delta.days == 1:
            time_ago = "1 day ago"
        elif delta.days < 7:
            time_ago = f"{delta.days} days ago"
        elif delta.days < 30:
            weeks = delta.days // 7
            time_ago = f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif delta.days < 365:
            months = delta.days // 30
            time_ago = f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = delta.days // 365
            time_ago = f"{years} year{'s' if years > 1 else ''} ago"

        tk.Label(
            info_frame,
            text=f"Last password change: {last_change.strftime('%m/%d/%Y')} - {time_ago}",
            font=("Arial", 9, "italic"),
            bg="#f9f9f9",
            fg="#666666"
        ).pack(side=tk.LEFT)

    def copy_to_clipboard(self, text, field_name):
        """Copy text to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(text)
        # Optional: Show brief confirmation
        print(f"{field_name} copied to clipboard")

    def open_website(self, url):
        """Open website URL in default browser."""
        import webbrowser
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        webbrowser.open(url)

    def edit_account(self, account_id):
        """Open edit window for an account."""
        account = self.account_manager.get_account(account_id)
        if account:
            from ui_account import AccountWindow
            AccountWindow(
                self,
                self.account_manager,
                mode="edit",
                account_data=account,
                callback=self.refresh_accounts
            )

    def delete_account(self, account_id):
        """Delete an account with confirmation."""
        from tkinter import messagebox

        # Get account name for confirmation
        account = self.account_manager.get_account(account_id)
        if not account:
            return

        # Show confirmation dialog with custom title
        result = messagebox.askyesno(
            "DELETE",
            f"Are you sure you want to delete '{account['account_name']}'?\n\n"
            "This action cannot be undone!",
            icon='warning'
        )

        if result:
            success = self.account_manager.delete_account(account_id)
            if success:
                self.refresh_accounts()
            else:
                messagebox.showerror("Error", "Failed to delete account.")

    # ------------------------------------------------------------------
    # Button command methods
    # ------------------------------------------------------------------

    def open_new_account(self):
        """Open new account creation window."""
        from ui_account import AccountWindow
        AccountWindow(
            self,
            self.account_manager,
            mode="create",
            callback=self.refresh_accounts
        )

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
            # Time's up - close app FIRST, then show message
            if hasattr(self, 'timer_id'):
                self.after_cancel(self.timer_id)

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

            # Withdraw (hide) main menu before showing message
            self.withdraw()

            # Show timeout message
            from tkinter import messagebox
            messagebox.showinfo("Session Expired", "Your session has expired. Please log in again.")

            # Destroy main menu
            self.destroy()

            # Show login window again if it exists
            if self.login_window is not None:
                self.login_window.deiconify()
                self.login_window.show_initial_screen()

    def _format_time(self, seconds):
        """Format seconds into a readable time string."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"Time until auto log-out: {minutes}m {secs}s"

    def _on_window_resize(self, event):
        """Handle window resize events to refresh grid layout."""
        # Only respond to main window resize, not child widgets
        if event.widget == self:
            # Cancel previous timer if exists
            if self._resize_timer:
                self.after_cancel(self._resize_timer)

            # Set a new timer to refresh after resize completes (debounce)
            self._resize_timer = self.after(200, self._refresh_on_resize)

    def _refresh_on_resize(self):
        """Refresh account grid after window resize."""
        self.refresh_accounts()


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()