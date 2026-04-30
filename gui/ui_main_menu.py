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
        self.configure(bg="#23272a")  # Dark gray background

        # Store user info and login window reference
        self.username = username
        self.login_window = login_window
        self.master_password = master_password

        # Initialize settings manager and override auto-logout from settings
        from services.settings import SettingsManager
        self.settings_manager = SettingsManager(username)
        settings_logout = self.settings_manager.get_auto_logout_time()
        if settings_logout and settings_logout > 0:
            auto_logout_time = settings_logout

        self.auto_logout_time = auto_logout_time  # in seconds
        self.time_remaining = auto_logout_time

        # Initialize account manager
        from services.account import AccountManager
        self.account_manager = AccountManager(username, master_password)

        # Track clipboard auto-clear scheduler id and fingerprint
        self._clipboard_clear_after_id = None
        self._clipboard_expected_text = None

        # Store reference to opened windows
        self.password_generator_window = None
        self.password_auditor_window = None
        self.settings_window = None

        self.create_header()
        self.create_main_content()

        # Bind window resize to refresh grid layout
        self.bind("<Configure>", self._on_window_resize)
        self._resize_timer = None

        # Reset auto-logout timer on any user input
        self.bind_all("<Key>", self._reset_timer)
        self.bind_all("<Button>", self._reset_timer)

        # Start the auto-logout timer
        self.start_timer()

    def create_header(self):
        """Create the header with logo, user info, and action buttons."""
        header_frame = tk.Frame(self, bg="#2c2f33", height=100, relief=tk.RAISED, borderwidth=1)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)

        # Left side - User info
        left_frame = tk.Frame(header_frame, bg="#2c2f33")
        left_frame.pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            left_frame,
            text=f"Logged in as: {self.username}",
            font=("Arial", 11),
            bg="#2c2f33",
            fg="#ffffff",
            anchor="w"
        ).pack(anchor="w")

        # Timer label that will be updated
        self.timer_label = tk.Label(
            left_frame,
            text=self._format_time(self.time_remaining),
            font=("Arial", 11),
            bg="#2c2f33",
            fg="#ffffff",
            anchor="w"
        )
        self.timer_label.pack(anchor="w", pady=(5, 0))

        # Center - PNG Logo (replace 'logo.png' with your file)
        try:
            from tkinter import PhotoImage
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            self.logo_img = PhotoImage(file=logo_path)
            logo_label = tk.Label(header_frame, image=self.logo_img, bg="#2c2f33")
            logo_label.pack(side=tk.LEFT, expand=True)
        except Exception as e:
            # If logo not found, show nothing (or fallback text)
            logo_label = tk.Label(header_frame, text="", bg="#2c2f33")
            logo_label.pack(side=tk.LEFT, expand=True)

        # Right side - Action buttons
        buttons_frame = tk.Frame(header_frame, bg="#2c2f33")
        buttons_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        # All buttons use the same blue color for consistency
        blue_color = "#2196F3"
        buttons = [
            ("+", "New Account.", self.open_new_account, blue_color),
            ("💡", "PW Generator", self.open_password_generator, blue_color),
            ("🔍", "PW audit.", self.open_password_auditor, blue_color),
            ("⚙", "Settings.", self.open_settings, blue_color),
            ("→", "Log out.", self.logout, blue_color)
        ]

        for symbol, label_text, command, color in buttons:
            self.create_text_button(buttons_frame, symbol, label_text, command, color)

    def create_text_button(self, parent, symbol, label_text, command, color):
        """Create a text-based button with symbol and label."""
        button_frame = tk.Frame(parent, bg="#2c2f33")
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
            bg="#2c2f33",
            fg="#ffffff"
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

    # ------------------------------------------------------------------
    # Sorting (driven by settings)
    # ------------------------------------------------------------------
    def _sort_accounts(self, accounts):
        """Sort accounts according to the user's settings."""
        sort_by = self.settings_manager.get_account_sort_by()

        if sort_by == "alphabetical":
            return sorted(accounts, key=lambda x: x.get("account_name", "").lower())
        if sort_by == "date_created":
            return sorted(accounts, key=lambda x: x.get("created_date", ""), reverse=True)
        if sort_by == "date_modified":
            return sorted(accounts, key=lambda x: x.get("last_modified", ""), reverse=True)
        if sort_by == "last_copied":
            return sorted(accounts, key=lambda x: x.get("last_copied") or "", reverse=True)
        return accounts

    def refresh_accounts(self):
        """Load accounts and refresh the display."""
        # Clear existing account cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Load accounts from manager, then sort
        accounts = self.account_manager.get_all_accounts()
        print(f"[DEBUG] refresh_accounts: loaded {len(accounts)} accounts for user {self.username}")
        accounts = self._sort_accounts(accounts)

        if not accounts:
            print("[DEBUG] No accounts found. Displaying empty state message.")
            tk.Label(
                self.scrollable_frame,
                text="No accounts yet.\n\nClick the '+' button to create your first account!",
                font=("Arial", 14),
                bg="#ffffff",
                fg="#888888"
            ).grid(row=0, column=0, pady=100, padx=100)
        else:
            print(f"[DEBUG] Displaying {len(accounts)} account cards.")
            # Calculate number of columns based on window width
            window_width = self.winfo_width()
            if window_width < 100:
                window_width = 1200

            available_width = window_width - 60
            card_width = 400
            num_columns = max(1, available_width // card_width)

            for index, account in enumerate(accounts):
                row = index // num_columns
                col = index % num_columns
                self.create_account_card(account, row, col)

            for col in range(num_columns):
                self.scrollable_frame.grid_columnconfigure(col, weight=1, uniform="column")

    def create_account_card(self, account, row, col):
        """Create a card widget for an account entry."""
        from datetime import datetime

        # Card frame
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
            command=lambda: self.copy_to_clipboard(
                account["username"], "Username", account_id=account["id"]
            ),
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

        show_password = [False]

        def toggle_password_visibility():
            if show_password[0]:
                password_var.set("*" * 10)
                show_btn.config(text="👁")
                show_password[0] = False
            else:
                password_var.set(account["password"])
                show_btn.config(text="👁‍🗨")
                show_password[0] = True
            password_display.update_idletasks()

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

        # Copy password button - passes account_id so we can track last_copied
        tk.Button(
            password_frame,
            text="📋",
            command=lambda: self.copy_to_clipboard(
                account["password"], "Password", account_id=account["id"]
            ),
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

        # Bottom info row - password age with renewal color coding
        info_frame = tk.Frame(card, bg="#f9f9f9")
        info_frame.pack(fill=tk.X, padx=15, pady=(5, 10))

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

        # Determine color based on password renewal setting
        renewal_days = self.settings_manager.get_password_renewal_days()
        text_color = "#666666"  # default gray

        if renewal_days > 0:
            age_days = delta.days
            t1 = renewal_days / 3.0
            t2 = (renewal_days / 3.0) * 2.0
            if age_days > renewal_days:
                text_color = "#F44336"   # red - overdue
            elif age_days > t2:
                text_color = "#FB8C00"   # orange - last third
            elif age_days > t1:
                text_color = "#F9A825"   # yellow - middle third
            # first third -> stays gray

        tk.Label(
            info_frame,
            text=f"Last password change: {last_change.strftime('%m/%d/%Y')} - {time_ago}",
            font=("Arial", 9, "italic"),
            bg="#f9f9f9",
            fg=text_color
        ).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Clipboard (with auto-clear + last_copied tracking)
    # ------------------------------------------------------------------
    def copy_to_clipboard(self, text, field_name, account_id=None):
        """Copy text to clipboard, track last_copied, schedule auto-clear."""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()  # Force clipboard to sync
        print(f"{field_name} copied to clipboard")

        # Track last_copied for sorting (for both username and password copies).
        if account_id is not None:
            try:
                self.account_manager.update_last_copied(account_id)
                # If currently sorting by last_copied, refresh order
                if self.settings_manager.get_account_sort_by() == "last_copied":
                    self.refresh_accounts()
            except Exception as e:
                print(f"[main_menu] update_last_copied failed: {e}")

        # Cancel any previously scheduled clear
        if self._clipboard_clear_after_id is not None:
            try:
                self.after_cancel(self._clipboard_clear_after_id)
            except Exception:
                pass
            self._clipboard_clear_after_id = None

        # Schedule auto-clear
        clear_seconds = self.settings_manager.get_clipboard_autoclear_seconds()
        if clear_seconds and clear_seconds > 0:
            self._clipboard_expected_text = text
            self._clipboard_clear_after_id = self.after(
                clear_seconds * 1000, self._clipboard_auto_clear
            )

    def _clipboard_auto_clear(self):
        """Clear clipboard if the text we copied is still on it."""
        self._clipboard_clear_after_id = None
        try:
            current = self.clipboard_get()
        except tk.TclError:
            current = None
        if current == self._clipboard_expected_text:
            # On Windows, ``clipboard_clear()`` alone does NOT actually
            # wipe the OS clipboard -- the contents linger until something
            # else takes ownership of the clipboard. The reliable fix is
            # to clear, write a single empty string, and then call
            # update() to push the change through.
            try:
                self.clipboard_clear()
                self.clipboard_append("")
                self.update()
                # Verify
                try:
                    after = self.clipboard_get()
                except tk.TclError:
                    after = ""
                if after:
                    print(
                        f"[main_menu] Clipboard auto-clear left text behind "
                        f"(len={len(after)}); retrying."
                    )
                    self.clipboard_clear()
                    self.clipboard_append(" ")
                    self.update()
                print("Clipboard auto-cleared for security")
            except Exception as e:
                print(f"[main_menu] Clipboard auto-clear failed: {e}")
        self._clipboard_expected_text = None

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
                callback=self.refresh_accounts,
                settings_manager=self.settings_manager,
            )

    def delete_account(self, account_id):
        """Delete an account with confirmation."""
        from tkinter import messagebox

        account = self.account_manager.get_account(account_id)
        if not account:
            return

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
            callback=self.refresh_accounts,
            settings_manager=self.settings_manager,
        )

    def open_password_generator(self):
        """Open the password generator window."""
        if self.password_generator_window is not None:
            try:
                self.password_generator_window.lift()
                self.password_generator_window.focus_force()
                return
            except tk.TclError:
                pass

        try:
            from ui_password_generator import PasswordGeneratorApp
            self.password_generator_window = PasswordGeneratorApp()
        except ImportError as e:
            print(f"Error importing password generator: {e}")
            print("Make sure ui_password_generator.py exists in the gui folder")

    def open_password_auditor(self):
        """Open password auditor window."""
        if self.password_auditor_window is not None:
            try:
                self.password_auditor_window.lift()
                self.password_auditor_window.focus_force()
                return
            except tk.TclError:
                pass

        try:
            from ui_password_auditor import PasswordAuditorApp
            self.password_auditor_window = PasswordAuditorApp()
        except ImportError as e:
            print(f"Error importing password auditor: {e}")
            print("Make sure ui_password_auditor.py exists in the gui folder")

    def open_settings(self):
        """Open the settings window."""
        # If already open, just raise it
        if self.settings_window is not None:
            try:
                self.settings_window.lift()
                self.settings_window.focus_force()
                return
            except tk.TclError:
                self.settings_window = None

        # We need the LoginManager to change master password
        from services.login import LoginManager
        login_manager = LoginManager()

        from ui_settings import SettingsWindow
        self.settings_window = SettingsWindow(
            self,
            username=self.username,
            settings_manager=self.settings_manager,
            account_manager=self.account_manager,
            login_manager=login_manager,
            master_password=self.master_password,
            callback=self.refresh_accounts,
        )

        # Clear reference when window closes
        def _on_close():
            try:
                self.settings_window.destroy()
            finally:
                self.settings_window = None

        self.settings_window.protocol("WM_DELETE_WINDOW", _on_close)

    def logout(self):
        """Handle logout."""
        if hasattr(self, 'timer_id'):
            self.after_cancel(self.timer_id)

        # Cancel any pending clipboard auto-clear
        if self._clipboard_clear_after_id is not None:
            try:
                self.after_cancel(self._clipboard_clear_after_id)
            except Exception:
                pass
            self._clipboard_clear_after_id = None

        # Close any open child windows
        for attr in ("password_generator_window", "password_auditor_window", "settings_window"):
            w = getattr(self, attr, None)
            if w is not None:
                try:
                    w.destroy()
                except Exception:
                    pass

        # Destroy main menu
        self.destroy()

        # Show login window again if it exists
        if self.login_window is not None:
            self.login_window.deiconify()
            self.login_window.show_initial_screen()

    # ------------------------------------------------------------------
    # Auto-logout timer
    # ------------------------------------------------------------------
    def start_timer(self):
        """Start the auto-logout countdown timer."""
        self.update_timer()

    def _reset_timer(self, event=None):
        """Reset the countdown on any user input."""
        self.time_remaining = self.auto_logout_time
        if hasattr(self, "timer_label"):
            try:
                self.timer_label.config(text=self._format_time(self.time_remaining))
            except tk.TclError:
                pass

    def update_timer(self):
        """Update the timer display and handle auto-logout."""
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self.timer_label.config(text=self._format_time(self.time_remaining))
            self.timer_id = self.after(1000, self.update_timer)
        else:
            # Time's up - close app FIRST, then show message
            if hasattr(self, 'timer_id'):
                self.after_cancel(self.timer_id)

            # Close any open child windows
            for attr in ("password_generator_window", "password_auditor_window", "settings_window"):
                w = getattr(self, attr, None)
                if w is not None:
                    try:
                        w.destroy()
                    except Exception:
                        pass

            self.withdraw()

            from tkinter import messagebox
            messagebox.showinfo("Session Expired", "Your session has expired. Please log in again.")

            self.destroy()

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
        if event.widget == self:
            if self._resize_timer:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(200, self._refresh_on_resize)

    def _refresh_on_resize(self):
        """Refresh account grid after window resize."""
        self.refresh_accounts()


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()
