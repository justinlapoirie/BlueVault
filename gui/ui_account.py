import tkinter as tk
from tkinter import messagebox
import sys
import os

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui_controller import theme


class AccountWindow(tk.Toplevel):
    """Window for creating or editing password vault accounts."""

    def __init__(self, master, account_manager, mode="create",
                 account_data=None, callback=None, settings_manager=None):
        """
        Initialize the account window.

        Args:
            master: Parent window
            account_manager: AccountManager instance
            mode: "create" or "edit"
            account_data: Existing account data (for edit mode)
            callback: Function to call after save
            settings_manager: Optional SettingsManager for password strength
                              enforcement.
        """
        super().__init__(master)

        self.account_manager = account_manager
        self.mode = mode
        self.account_data = account_data
        self.callback = callback
        self.settings_manager = settings_manager

        # Window configuration
        if mode == "create":
            self.title("New Account - BlueVault")
        else:
            self.title("Edit Account - BlueVault")

        self.geometry("520x660")
        self.resizable(False, False)
        self.configure(bg=theme["app_bg"])

        # Make window modal
        self.transient(master)
        self.grab_set()

        self.create_widgets()

        # Populate fields if editing
        if mode == "edit" and account_data:
            self.populate_fields(account_data)

        # Live theme updates
        theme.subscribe(self._apply_theme)
        self.bind("<Destroy>", self._on_destroy, add="+")

    # ------------------------------------------------------------------
    # Theme integration
    # ------------------------------------------------------------------
    def _apply_theme(self):
        """Repaint by saving form state, rebuilding widgets, restoring."""
        try:
            saved = self._snapshot_form()
            for child in self.winfo_children():
                child.destroy()
            self.configure(bg=theme["app_bg"])
            self.create_widgets()
            self._restore_form(saved)
        except tk.TclError:
            pass

    def _snapshot_form(self) -> dict:
        try:
            return {
                "account_name": self.account_name_entry.get(),
                "username": self.username_entry.get(),
                "password": self.password_entry.get(),
                "website": self.website_entry.get(),
                "notes": self.notes_text.get(1.0, tk.END).rstrip("\n"),
                "show_password": bool(self.show_password_var.get()),
            }
        except (AttributeError, tk.TclError):
            return {}

    def _restore_form(self, data: dict) -> None:
        if not data:
            return
        try:
            self.account_name_entry.delete(0, tk.END)
            self.account_name_entry.insert(0, data.get("account_name", ""))
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, data.get("username", ""))
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, data.get("password", ""))
            self.website_entry.delete(0, tk.END)
            self.website_entry.insert(0, data.get("website", ""))
            self.notes_text.delete(1.0, tk.END)
            self.notes_text.insert(1.0, data.get("notes", ""))
            self.show_password_var.set(data.get("show_password", False))
            self.toggle_password()
        except (AttributeError, tk.TclError):
            pass

    def _on_destroy(self, event):
        if event.widget is self:
            theme.unsubscribe(self._apply_theme)

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------
    def create_widgets(self):
        """Create all form widgets."""
        # Title
        title_text = "Create New Account" if self.mode == "create" else "Edit Account"
        tk.Label(
            self,
            text=title_text,
            font=("Segoe UI", 17, "bold"),
            bg=theme["app_bg"],
            fg=theme["accent"],
        ).pack(pady=(20, 4))

        # Thin accent divider
        tk.Frame(self, bg=theme["accent"], height=2).pack(fill=tk.X, padx=40)

        # Scrollable form area
        form_frame = tk.Frame(
            self,
            bg=theme["app_bg"],
        )
        form_frame.pack(pady=14, padx=40, fill=tk.BOTH, expand=True)

        # Account Name (Required)
        self._field_label(form_frame, "Account Name *", row=0)
        self.account_name_entry = tk.Entry(
            form_frame, font=("Segoe UI", 11), width=40, **theme.entry_style()
        )
        self.account_name_entry.grid(row=1, column=0, pady=(0, 16), sticky="ew")
        self.account_name_entry.focus()
        self._bind_focus_highlight(self.account_name_entry)

        # Username (Required)
        self._field_label(form_frame, "Username / Email *", row=2)
        self.username_entry = tk.Entry(
            form_frame, font=("Segoe UI", 11), width=40, **theme.entry_style()
        )
        self.username_entry.grid(row=3, column=0, pady=(0, 16), sticky="ew")
        self._bind_focus_highlight(self.username_entry)

        # Password (Required)
        password_label_frame = tk.Frame(form_frame, bg=theme["app_bg"])
        password_label_frame.grid(row=4, column=0, sticky="w", pady=(0, 5))

        tk.Label(
            password_label_frame,
            text="Password *",
            font=("Segoe UI", 10, "bold"),
            bg=theme["app_bg"],
            fg=theme["text_primary"],
        ).pack(side=tk.LEFT)

        if self.settings_manager is not None:
            req = self.settings_manager.get_password_strength_requirement()
            if req and req.lower() != "off":
                tk.Label(
                    password_label_frame,
                    text=f"  (min: {req.capitalize()})",
                    font=("Segoe UI", 8, "italic"),
                    bg=theme["app_bg"],
                    fg=theme["text_muted"],
                ).pack(side=tk.LEFT)

        password_container = tk.Frame(form_frame, bg=theme["app_bg"])
        password_container.grid(row=5, column=0, pady=(0, 16), sticky="ew")

        self.password_entry = tk.Entry(
            password_container,
            font=("Segoe UI", 11),
            width=26,
            show="*",
            **theme.entry_style(),
        )
        self.password_entry.pack(side=tk.LEFT, padx=(0, 6))
        self._bind_focus_highlight(self.password_entry)

        gen_btn_style = theme.primary_button_style()
        gen_btn_style.update(font=("Segoe UI", 9, "bold"), padx=8, pady=2)
        tk.Button(
            password_container,
            text="🔑 Generate",
            command=self.generate_password,
            **gen_btn_style,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.show_password_var = tk.BooleanVar(master=self, value=False)
        self.show_password_checkbox = tk.Checkbutton(
            password_container,
            text="Show",
            variable=self.show_password_var,
            command=self.toggle_password,
            font=("Segoe UI", 9),
            **theme.checkbutton_style(on="app_bg"),
        )
        self.show_password_checkbox.pack(side=tk.LEFT)

        # Website URL (Optional)
        self._field_label(form_frame, "Website URL  (optional)", row=6, bold=False)
        self.website_entry = tk.Entry(
            form_frame, font=("Segoe UI", 11), width=40, **theme.entry_style()
        )
        self.website_entry.grid(row=7, column=0, pady=(0, 16), sticky="ew")
        self._bind_focus_highlight(self.website_entry)

        # Notes (Optional)
        self._field_label(form_frame, "Notes  (optional)", row=8, bold=False)
        self.notes_text = tk.Text(
            form_frame,
            font=("Segoe UI", 10),
            width=40,
            height=4,
            wrap=tk.WORD,
            **theme.text_style(),
        )
        self.notes_text.grid(row=9, column=0, pady=(0, 10), sticky="ew")

        tk.Label(
            form_frame,
            text="* Required",
            font=("Segoe UI", 8, "italic"),
            bg=theme["app_bg"],
            fg=theme["text_muted"],
        ).grid(row=10, column=0, sticky="w")

        # ── Bottom-right action buttons ─────────────────────────────────
        btn_strip = tk.Frame(self, bg=theme["app_bg"])
        btn_strip.pack(fill=tk.X, padx=40, pady=(8, 18))

        cancel_style = theme.secondary_button_style()
        cancel_style.update(font=("Segoe UI", 10), padx=16, pady=6)

        save_style = theme.primary_button_style()
        save_style.update(font=("Segoe UI", 10, "bold"), padx=16, pady=6)

        tk.Button(
            btn_strip,
            text="Cancel",
            command=self.destroy,
            **cancel_style,
        ).pack(side=tk.RIGHT, padx=(6, 0))

        tk.Button(
            btn_strip,
            text="Save",
            command=self.save_account,
            **save_style,
        ).pack(side=tk.RIGHT)

    def _bind_focus_highlight(self, entry):
        """Make entry border glow accent color on focus."""
        border_normal = theme["input_border"]
        border_focus  = theme.color("input_focus_border", theme["accent"])
        entry.bind("<FocusIn>",  lambda e: entry.config(
            highlightbackground=border_focus, highlightcolor=border_focus))
        entry.bind("<FocusOut>", lambda e: entry.config(
            highlightbackground=border_normal, highlightcolor=border_focus))

    def _field_label(self, parent, text, row, bold=True):
        font = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
        tk.Label(
            parent,
            text=text,
            font=font,
            bg=theme["app_bg"],
            fg=theme["text_primary"],
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=(0, 4))

    def toggle_password(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def generate_password(self):
        """Generate a new password and insert it into the password entry."""
        try:
            from services.password_generator import PasswordGenerator
            generator = PasswordGenerator(
                length=12,
                include_uppercase=True,
                include_lowercase=True,
                include_digits=True,
                include_symbols=True,
            )
            password = generator.generate_password()
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, password)
            self.show_password_var.set(True)
            self.toggle_password()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate password: {str(e)}")

    def populate_fields(self, account_data):
        """Populate form fields with existing account data."""
        self.account_name_entry.insert(0, account_data.get("account_name", ""))
        self.username_entry.insert(0, account_data.get("username", ""))
        self.password_entry.insert(0, account_data.get("password", ""))
        self.website_entry.insert(0, account_data.get("website_url", ""))
        self.notes_text.insert(1.0, account_data.get("notes", ""))

    def save_account(self):
        """Save the account (create or update)."""
        # Get form values
        account_name = self.account_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        website_url = self.website_entry.get().strip()
        notes = self.notes_text.get(1.0, tk.END).strip()

        # Validation
        if not account_name:
            messagebox.showerror("Error", "Account name is required.")
            self.account_name_entry.focus()
            return

        if not username:
            messagebox.showerror("Error", "Username/Email is required.")
            self.username_entry.focus()
            return

        if not password:
            messagebox.showerror("Error", "Password is required.")
            self.password_entry.focus()
            return

        # Enforce password strength requirement (if settings are available).
        # Only enforce when the password has actually been set/changed in edit
        # mode, so that editing an old account that doesn't meet the new
        # requirement is still allowed (as long as the password isn't touched).
        should_check = True
        if self.mode == "edit" and self.account_data is not None:
            if password == self.account_data.get("password"):
                should_check = False

        if should_check and self.settings_manager is not None:
            req = self.settings_manager.get_password_strength_requirement()
            print(
                f"[ui_account] enforcing strength requirement "
                f"{req!r} on save (mode={self.mode})"
            )

            # Import here so a missing utils module surfaces loudly.
            try:
                from utils.entropy_calculator import meets_strength_requirement
            except ImportError as e:
                messagebox.showerror(
                    "Internal error",
                    f"Could not load password strength checker:\n{e}",
                    parent=self,
                )
                return

            ok, msg = meets_strength_requirement(password, req)
            print(f"[ui_account] strength check -> ok={ok}, msg={msg!r}")
            if not ok:
                messagebox.showerror("Weak Password", msg, parent=self)
                self.password_entry.focus()
                return

        # Save account
        try:
            if self.mode == "create":
                result = self.account_manager.create_account(
                    account_name=account_name,
                    username=username,
                    password=password,
                    notes=notes,
                    website_url=website_url,
                )

                if result:
                    messagebox.showinfo("Success", "Account created successfully!")
                else:
                    messagebox.showerror("Error", "Failed to create account.")
                    return

            else:  # edit mode
                result = self.account_manager.update_account(
                    self.account_data["id"],
                    account_name=account_name,
                    username=username,
                    password=password,
                    notes=notes,
                    website_url=website_url,
                )

                if result:
                    messagebox.showinfo("Success", "Account updated successfully!")
                else:
                    messagebox.showerror("Error", "Failed to update account.")
                    return

            if self.callback:
                self.callback()

            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")


# For standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from services.account import AccountManager

    manager = AccountManager("testuser", "testpass")

    app = AccountWindow(root, manager, mode="create")
    app.mainloop()
