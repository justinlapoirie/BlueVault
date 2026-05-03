import tkinter as tk
import sys
import os

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui_controller import theme


class MainMenu(tk.Tk):
    def __init__(self, username="User", login_window=None, auto_logout_time=300, master_password=None):
        super().__init__()
        self.title("BlueVault")
        self.geometry("1100x700")

        # Store user info and login window reference
        self.username = username
        self.login_window = login_window
        self.master_password = master_password

        # Initialize settings manager and override auto-logout from settings
        from services.settings import SettingsManager
        self.settings_manager = SettingsManager(username)

        # Bind the theme controller to this user's settings (loads + persists).
        theme.attach_settings(self.settings_manager)
        theme.configure_ttk(self)
        self.configure(bg=theme["app_bg"])

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

        # Build initial UI
        self._build_widgets()

        # Bind window resize to refresh grid layout
        self.bind("<Configure>", self._on_window_resize)
        self._resize_timer = None

        # Reset auto-logout timer on any user input
        self.bind_all("<Key>", self._reset_timer)
        self.bind_all("<Button>", self._reset_timer)

        # Start the auto-logout timer
        self.start_timer()

        # Subscribe to live theme changes (re-paint when settings flip
        # dark <-> light). Unsubscribe on destroy.
        theme.subscribe(self._apply_theme)
        self.bind("<Destroy>", self._on_destroy, add="+")

    # ------------------------------------------------------------------
    # Theme integration
    # ------------------------------------------------------------------
    def _build_widgets(self):
        """(Re)create every child widget from scratch using current theme."""
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=theme["app_bg"])
        self._search_var = tk.StringVar(master=self)
        self._search_var.trace_add("write", lambda *_: self.refresh_accounts())
        self._create_layout()

    def _apply_theme(self):
        """Theme-change callback: rebuild header + content with new colors."""
        try:
            theme.configure_ttk(self)
            self._build_widgets()
        except tk.TclError:
            pass

    def _on_destroy(self, event):
        if event.widget is self:
            theme.unsubscribe(self._apply_theme)

    def _create_layout(self):
        """Build the two-pane layout: slim sidebar + content area."""
        # ── outer container fills the whole window
        outer = tk.Frame(self, bg=theme["app_bg"])
        outer.pack(fill=tk.BOTH, expand=True)

        # ── LEFT SIDEBAR ────────────────────────────────────────────────
        sidebar = tk.Frame(outer, bg=theme["sidebar_bg"], width=190)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Logo area
        logo_frame = tk.Frame(sidebar, bg=theme["sidebar_bg"])
        logo_frame.pack(fill=tk.X, pady=(20, 0))
        try:
            from tkinter import PhotoImage
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                self.logo_img = PhotoImage(file=logo_path)
                tk.Label(logo_frame, image=self.logo_img,
                         bg=theme["sidebar_bg"]).pack(pady=(0, 4))
        except Exception:
            pass
        tk.Label(
            logo_frame,
            text="BlueVault",
            font=("Segoe UI", 16, "bold"),
            bg=theme["sidebar_bg"],
            fg=theme["accent"],
        ).pack()

        # Thin separator
        tk.Frame(sidebar, bg=theme["sidebar_hover"], height=1).pack(
            fill=tk.X, pady=10, padx=12
        )

        # User info + timer
        info_frame = tk.Frame(sidebar, bg=theme["sidebar_bg"])
        info_frame.pack(fill=tk.X, padx=14, pady=(0, 8))
        tk.Label(
            info_frame,
            text=f"👤  {self.username}",
            font=("Segoe UI", 10, "bold"),
            bg=theme["sidebar_bg"],
            fg=theme["sidebar_fg"],
            anchor="w",
        ).pack(anchor="w")
        self.timer_label = tk.Label(
            info_frame,
            text=self._format_time(self.time_remaining),
            font=("Segoe UI", 8),
            bg=theme["sidebar_bg"],
            fg=theme["text_muted"],
            anchor="w",
            wraplength=160,
            justify="left",
        )
        self.timer_label.pack(anchor="w", pady=(3, 0))

        tk.Frame(sidebar, bg=theme["sidebar_hover"], height=1).pack(
            fill=tk.X, pady=8, padx=12
        )

        # Nav buttons
        nav_items = [
            ("＋", "New Account", self.open_new_account),
            ("💡", "PW Generator", self.open_password_generator),
            ("🔍", "PW Auditor",   self.open_password_auditor),
            ("⚙",  "Settings",    self.open_settings),
        ]
        for icon, label, cmd in nav_items:
            self._sidebar_button(sidebar, icon, label, cmd)

        # Logout pushed to bottom
        spacer = tk.Frame(sidebar, bg=theme["sidebar_bg"])
        spacer.pack(fill=tk.BOTH, expand=True)
        tk.Frame(sidebar, bg=theme["sidebar_hover"], height=1).pack(
            fill=tk.X, pady=8, padx=12
        )
        self._sidebar_button(sidebar, "→", "Log Out", self.logout, danger=True)

        # ── RIGHT CONTENT AREA ──────────────────────────────────────────
        content_outer = tk.Frame(outer, bg=theme["surface_bg"])
        content_outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Top bar: title + search
        top_bar = tk.Frame(content_outer, bg=theme["header_bg"])
        top_bar.pack(fill=tk.X, padx=0, pady=0)

        tk.Label(
            top_bar,
            text="My Vault",
            font=("Segoe UI", 15, "bold"),
            bg=theme["header_bg"],
            fg=theme["text_primary"],
        ).pack(side=tk.LEFT, padx=20, pady=14)

        # Search bar
        search_frame = tk.Frame(top_bar, bg=theme["header_bg"])
        search_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        tk.Label(
            search_frame,
            text="🔎",
            font=("Segoe UI", 11),
            bg=theme["header_bg"],
            fg=theme["text_muted"],
        ).pack(side=tk.LEFT, padx=(0, 4))

        search_entry = tk.Entry(
            search_frame,
            textvariable=self._search_var,
            font=("Segoe UI", 11),
            width=24,
            **theme.entry_style(),
        )
        search_entry.pack(side=tk.LEFT)
        search_entry.insert(0, "Search accounts…")
        search_entry.config(fg=theme["text_muted"])

        def _search_focus_in(e):
            if search_entry.get() == "Search accounts…":
                search_entry.delete(0, tk.END)
                search_entry.config(fg=theme["input_fg"])
                self._search_var.set("")

        def _search_focus_out(e):
            if not search_entry.get():
                search_entry.insert(0, "Search accounts…")
                search_entry.config(fg=theme["text_muted"])
                self._search_var.set("")

        search_entry.bind("<FocusIn>",  _search_focus_in)
        search_entry.bind("<FocusOut>", _search_focus_out)

        # Thin accent separator under top bar
        tk.Frame(content_outer, bg=theme["section_border"], height=2).pack(fill=tk.X)

        # Scrollable card area
        scroll_container = tk.Frame(content_outer, bg=theme["surface_bg"])
        scroll_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            scroll_container,
            bg=theme["surface_bg"],
            highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(
            scroll_container, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=theme["surface_bg"])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.refresh_accounts()

    # ------------------------------------------------------------------
    # Sidebar helper
    # ------------------------------------------------------------------
    def _sidebar_button(self, parent, icon, label, command, danger=False):
        """Create a full-width sidebar nav item with hover effect."""
        normal_bg  = theme["sidebar_bg"]
        hover_bg   = theme["sidebar_hover"]
        normal_fg  = theme["status_danger"] if danger else theme["sidebar_fg"]

        row = tk.Frame(parent, bg=normal_bg, cursor="hand2")
        row.pack(fill=tk.X, padx=8, pady=1)

        icon_lbl = tk.Label(row, text=icon,  font=("Segoe UI", 13),
                            bg=normal_bg, fg=normal_fg, width=3)
        icon_lbl.pack(side=tk.LEFT, padx=(6, 2), pady=8)

        text_lbl = tk.Label(row, text=label, font=("Segoe UI", 10),
                            bg=normal_bg, fg=normal_fg, anchor="w")
        text_lbl.pack(side=tk.LEFT, pady=8)

        def _on_enter(e):
            row.config(bg=hover_bg)
            icon_lbl.config(bg=hover_bg)
            text_lbl.config(bg=hover_bg)

        def _on_leave(e):
            row.config(bg=normal_bg)
            icon_lbl.config(bg=normal_bg)
            text_lbl.config(bg=normal_bg)

        def _on_click(e):
            command()

        for widget in (row, icon_lbl, text_lbl):
            widget.bind("<Enter>",   _on_enter)
            widget.bind("<Leave>",   _on_leave)
            widget.bind("<Button-1>", _on_click)

    # ------------------------------------------------------------------
    # Legacy stubs (called by _build_widgets in older code paths / tests)
    # ------------------------------------------------------------------
    def create_header(self):
        pass  # replaced by _create_layout

    def create_text_button(self, *args, **kwargs):
        pass  # replaced by _sidebar_button

    def create_main_content(self):
        pass  # replaced by _create_layout


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
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        accounts = self.account_manager.get_all_accounts()
        print(f"[DEBUG] refresh_accounts: loaded {len(accounts)} accounts for user {self.username}")
        accounts = self._sort_accounts(accounts)

        # Apply search filter
        query = getattr(self, "_search_var", None)
        if query:
            q = query.get().strip().lower()
            placeholder = "search accounts…"
            if q and q != placeholder:
                accounts = [
                    a for a in accounts
                    if q in a.get("account_name", "").lower()
                    or q in a.get("username", "").lower()
                    or q in (a.get("website_url") or "").lower()
                ]

        if not accounts:
            tk.Label(
                self.scrollable_frame,
                text="No accounts found.\n\nClick  ＋ New Account  in the sidebar to add one.",
                font=("Segoe UI", 13),
                bg=theme["surface_bg"],
                fg=theme["text_muted"],
                justify="center",
            ).grid(row=0, column=0, pady=120, padx=80)
        else:
            print(f"[DEBUG] Displaying {len(accounts)} account cards.")
            window_width = self.winfo_width()
            if window_width < 200:
                window_width = 1100
            available_width = window_width - 190 - 40  # sidebar + padding
            card_width = 380
            num_columns = max(1, available_width // card_width)

            for index, account in enumerate(accounts):
                row = index // num_columns
                col = index % num_columns
                self.create_account_card(account, row, col)

            for col in range(num_columns):
                self.scrollable_frame.grid_columnconfigure(
                    col, weight=1, uniform="column"
                )


    def create_account_card(self, account, row, col):
        """Create a modernised card widget for an account entry."""
        from datetime import datetime

        card_bg   = theme["card_bg"]
        card_inner = theme["card_inner_bg"]
        label_fg  = theme["card_label_fg"]
        accent_fg = theme["accent"]
        shadow    = theme.color("card_shadow", theme["app_bg"])

        # Outer wrapper gives the illusion of a shadow / elevation border
        wrapper = tk.Frame(
            self.scrollable_frame,
            bg=shadow,
            padx=1,
            pady=1,
        )
        wrapper.grid(row=row, column=col, padx=12, pady=10, sticky="nsew")

        card = tk.Frame(wrapper, bg=card_bg)
        card.pack(fill=tk.BOTH, expand=True)

        # ── Coloured accent strip along the left edge ──────────────────
        accent_bar = tk.Frame(card, bg=accent_fg, width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y)

        body = tk.Frame(card, bg=card_bg)
        body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=14, pady=12)

        # ── Account name (large + bold) + action buttons ───────────────
        top_row = tk.Frame(body, bg=card_bg)
        top_row.pack(fill=tk.X)

        tk.Label(
            top_row,
            text=account["account_name"],
            font=("Segoe UI", 14, "bold"),
            bg=card_bg,
            fg=theme["text_primary"],
            anchor="w",
        ).pack(side=tk.LEFT)

        action_frame = tk.Frame(top_row, bg=card_bg)
        action_frame.pack(side=tk.RIGHT)

        def _make_icon_btn(parent, text, fg, cmd):
            b = tk.Label(parent, text=text, font=("Segoe UI", 13),
                         bg=card_bg, fg=fg, cursor="hand2")
            b.pack(side=tk.LEFT, padx=4)
            b.bind("<Button-1>", lambda e: cmd())
            b.bind("<Enter>", lambda e: b.config(fg=accent_fg))
            b.bind("<Leave>", lambda e: b.config(fg=fg))
            return b

        _make_icon_btn(action_frame, "✏", label_fg,
                       lambda: self.edit_account(account["id"]))
        _make_icon_btn(action_frame, "🗑", theme["status_danger"],
                       lambda: self.delete_account(account["id"]))

        # ── Thin divider ───────────────────────────────────────────────
        tk.Frame(body, bg=theme.color("card_shadow", theme["app_bg"]),
                 height=1).pack(fill=tk.X, pady=(6, 8))

        # ── Field rows ─────────────────────────────────────────────────
        def _field_row(label_text, value_text, copy_value=None, secret=False):
            row_frame = tk.Frame(body, bg=card_bg)
            row_frame.pack(fill=tk.X, pady=3)

            tk.Label(
                row_frame,
                text=label_text,
                font=("Segoe UI", 9),
                bg=card_bg,
                fg=label_fg,
                width=11,
                anchor="w",
            ).pack(side=tk.LEFT)

            val_var = tk.StringVar(master=self,
                                   value="••••••••••" if secret else value_text)

            val_entry = tk.Entry(
                row_frame,
                textvariable=val_var,
                font=("Segoe UI", 10),
                bg=card_inner,
                fg=theme["input_fg"],
                readonlybackground=card_inner,
                relief=tk.FLAT,
                state="readonly",
                width=30,
                bd=0,
            )
            val_entry.pack(side=tk.LEFT, padx=(0, 4))

            if secret:
                visible = [False]

                def _toggle():
                    if visible[0]:
                        val_var.set("••••••••••")
                        eye_lbl.config(text="👁")
                        visible[0] = False
                    else:
                        val_var.set(value_text)
                        eye_lbl.config(text="👁‍🗨")
                        visible[0] = True

                eye_lbl = tk.Label(row_frame, text="👁", font=("Segoe UI", 10),
                                   bg=card_bg, fg=label_fg, cursor="hand2")
                eye_lbl.pack(side=tk.LEFT, padx=2)
                eye_lbl.bind("<Button-1>", lambda e: _toggle())

            if copy_value is not None:
                copy_lbl = tk.Label(row_frame, text="📋",
                                    font=("Segoe UI", 10),
                                    bg=card_bg, fg=label_fg, cursor="hand2")
                copy_lbl.pack(side=tk.LEFT, padx=2)

                def _copy(lbl=copy_lbl, val=copy_value, fname=label_text):
                    self.copy_to_clipboard(val, fname, account_id=account["id"])
                    self._show_copied_feedback(lbl)

                copy_lbl.bind("<Button-1>", lambda e, f=_copy: f())

        _field_row("Username", account["username"],
                   copy_value=account["username"])
        _field_row("Password", account["password"],
                   copy_value=account["password"], secret=True)

        if account.get("website_url"):
            url_row = tk.Frame(body, bg=card_bg)
            url_row.pack(fill=tk.X, pady=3)
            tk.Label(url_row, text="Website",
                     font=("Segoe UI", 9), bg=card_bg, fg=label_fg,
                     width=11, anchor="w").pack(side=tk.LEFT)
            url_lbl = tk.Label(url_row, text=account["website_url"],
                               font=("Segoe UI", 10, "underline"),
                               bg=card_bg, fg=accent_fg, cursor="hand2")
            url_lbl.pack(side=tk.LEFT)
            url_lbl.bind("<Button-1>",
                         lambda e: self.open_website(account["website_url"]))

        if account.get("notes"):
            notes_row = tk.Frame(body, bg=card_bg)
            notes_row.pack(fill=tk.X, pady=3)
            tk.Label(notes_row, text="Notes",
                     font=("Segoe UI", 9), bg=card_bg, fg=label_fg,
                     width=11, anchor="nw").pack(side=tk.LEFT, anchor="n")
            notes_box = tk.Text(notes_row, font=("Segoe UI", 9),
                                bg=card_inner, fg=theme["input_fg"],
                                height=2, width=30, wrap=tk.WORD,
                                relief=tk.FLAT, bd=0)
            notes_box.pack(side=tk.LEFT)
            notes_box.insert(1.0, account["notes"])
            notes_box.config(state="disabled")

        # ── Password age footer ────────────────────────────────────────
        last_change = datetime.fromisoformat(account["last_password_change"])
        delta = datetime.now() - last_change

        if delta.days == 0:       time_ago = "Today"
        elif delta.days == 1:     time_ago = "1 day ago"
        elif delta.days < 7:      time_ago = f"{delta.days} days ago"
        elif delta.days < 30:     time_ago = f"{delta.days // 7}w ago"
        elif delta.days < 365:    time_ago = f"{delta.days // 30}mo ago"
        else:                     time_ago = f"{delta.days // 365}y ago"

        renewal_days = self.settings_manager.get_password_renewal_days()
        age_color = theme["status_neutral"]
        if renewal_days > 0:
            t1, t2 = renewal_days / 3.0, (renewal_days / 3.0) * 2.0
            if delta.days > renewal_days:    age_color = theme["status_danger"]
            elif delta.days > t2:            age_color = theme["status_orange"]
            elif delta.days > t1:            age_color = theme["status_yellow"]

        tk.Frame(body, bg=theme.color("card_shadow", theme["app_bg"]),
                 height=1).pack(fill=tk.X, pady=(8, 4))
        tk.Label(
            body,
            text=f"Password changed: {last_change.strftime('%m/%d/%Y')}  ·  {time_ago}",
            font=("Segoe UI", 8, "italic"),
            bg=card_bg,
            fg=age_color,
            anchor="w",
        ).pack(anchor="w")

    # ------------------------------------------------------------------
    # Copy feedback micro-interaction
    # ------------------------------------------------------------------
    def _show_copied_feedback(self, label_widget):
        """Briefly show ✓ Copied on the given label widget."""
        original_text = label_widget.cget("text")
        label_widget.config(text="✓", fg=theme["status_success"])

        def _restore():
            try:
                label_widget.config(text=original_text,
                                    fg=theme["card_label_fg"])
            except tk.TclError:
                pass

        self.after(1200, _restore)



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
            icon='warning',
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
            self.password_generator_window = PasswordGeneratorApp(self)
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
            self.password_auditor_window = PasswordAuditorApp(self)
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

        # Theme controller cleanup
        theme.unsubscribe(self._apply_theme)

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
            try:
                self.timer_label.config(text=self._format_time(self.time_remaining))
            except tk.TclError:
                pass
            self.timer_id = self.after(1000, self.update_timer)
        else:
            if hasattr(self, 'timer_id'):
                self.after_cancel(self.timer_id)

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

            theme.unsubscribe(self._apply_theme)
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
