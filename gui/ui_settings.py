"""
Settings window for BlueVault.

Opened from the main menu's gear button. Provides dropdowns for the
configurable settings (auto-logout, password renewal, clipboard auto-
clear, password strength requirement, and account sorting), plus
buttons for change master password, export vault, and import vault.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Ensure parent directory is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.settings import (
    AUTO_LOGOUT_OPTIONS,
    PASSWORD_RENEWAL_OPTIONS,
    CLIPBOARD_AUTOCLEAR_OPTIONS,
    PASSWORD_STRENGTH_OPTIONS,
    SORT_BY_OPTIONS,
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _label_for_value(options: dict, value):
    """Reverse-lookup a display label for a stored value."""
    for label, v in options.items():
        if v == value:
            return label
    # Fallback: first option
    return next(iter(options.keys()))


# -----------------------------------------------------------------------------
# Main settings window
# -----------------------------------------------------------------------------
class SettingsWindow(tk.Toplevel):
    """Top-level settings window."""

    def __init__(self, master, username, settings_manager, account_manager,
                 login_manager, master_password=None, callback=None):
        super().__init__(master)

        self.username = username
        self.settings_manager = settings_manager
        self.account_manager = account_manager
        self.login_manager = login_manager
        self.master_password = master_password
        self.callback = callback

        self.title(f"Settings - {username} - BlueVault")
        self.geometry("640x720")
        self.configure(bg="#f0f0f0")
        self.resizable(False, True)

        # Make modal-ish
        self.transient(master)
        self.grab_set()

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Title
        tk.Label(
            self,
            text="Settings",
            font=("Arial", 20, "bold"),
            bg="#f0f0f0",
        ).pack(pady=(18, 6))

        tk.Label(
            self,
            text=f"Logged in as: {self.username}",
            font=("Arial", 10, "italic"),
            bg="#f0f0f0",
            fg="#666666",
        ).pack(pady=(0, 10))

        # Scrollable container so the window stays usable on smaller screens
        container = tk.Frame(self, bg="#f0f0f0")
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        canvas = tk.Canvas(container, bg="#f0f0f0", highlightthickness=0)
        scroll = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="#f0f0f0")

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Sections
        self._build_security_section(inner)
        self._build_organization_section(inner)
        self._build_master_password_section(inner)
        self._build_vault_section(inner)

        # Bottom action bar (always visible)
        action_bar = tk.Frame(self, bg="#f0f0f0")
        action_bar.pack(fill=tk.X, padx=16, pady=(6, 16))

        tk.Button(
            action_bar,
            text="Save Settings",
            command=self._on_save,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=16,
            cursor="hand2",
        ).pack(side=tk.RIGHT, padx=(6, 0))

        tk.Button(
            action_bar,
            text="Close",
            command=self.destroy,
            font=("Arial", 12),
            bg="#9E9E9E",
            fg="white",
            width=10,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Section: Security (auto-logout, renewal, clipboard, strength)
    # ------------------------------------------------------------------
    def _build_security_section(self, parent):
        frame = self._make_section(parent, "Security")

        # Auto-logout
        self.auto_logout_var = tk.StringVar(
            value=_label_for_value(
                AUTO_LOGOUT_OPTIONS,
                self.settings_manager.get_auto_logout_time(),
            )
        )
        self._make_dropdown(
            frame,
            label="Global auto-logout timer",
            description=(
                "Close the app and return to the login screen after this much "
                "inactivity. Any key press or click resets the timer."
            ),
            variable=self.auto_logout_var,
            options=list(AUTO_LOGOUT_OPTIONS.keys()),
        )

        # Password renewal
        self.renewal_var = tk.StringVar(
            value=_label_for_value(
                PASSWORD_RENEWAL_OPTIONS,
                self.settings_manager.get_password_renewal_days(),
            )
        )
        self._make_dropdown(
            frame,
            label="Password renewal reminder",
            description=(
                "Color-codes the 'last password change' text on each account "
                "card. Yellow after a third of the interval has elapsed, "
                "orange after two-thirds, red past the full interval."
            ),
            variable=self.renewal_var,
            options=list(PASSWORD_RENEWAL_OPTIONS.keys()),
        )

        # Clipboard auto-clear
        self.clipboard_var = tk.StringVar(
            value=_label_for_value(
                CLIPBOARD_AUTOCLEAR_OPTIONS,
                self.settings_manager.get_clipboard_autoclear_seconds(),
            )
        )
        self._make_dropdown(
            frame,
            label="Clipboard auto-clear",
            description=(
                "How long after copying a username or password to keep it on "
                "the clipboard before wiping it. Choose 'Never' to disable."
            ),
            variable=self.clipboard_var,
            options=list(CLIPBOARD_AUTOCLEAR_OPTIONS.keys()),
        )

        # Password strength requirement
        self.strength_var = tk.StringVar(
            value=_label_for_value(
                PASSWORD_STRENGTH_OPTIONS,
                self.settings_manager.get_password_strength_requirement(),
            )
        )
        self._make_dropdown(
            frame,
            label="Password strength requirement",
            description=(
                "Minimum strength required when creating or updating an "
                "account password. 'Low' requires a Moderate rating or "
                "better; 'Strong' requires a Strong rating."
            ),
            variable=self.strength_var,
            options=list(PASSWORD_STRENGTH_OPTIONS.keys()),
        )

    # ------------------------------------------------------------------
    # Section: Organization (sort by)
    # ------------------------------------------------------------------
    def _build_organization_section(self, parent):
        frame = self._make_section(parent, "Account Organization")

        self.sort_var = tk.StringVar(
            value=_label_for_value(
                SORT_BY_OPTIONS,
                self.settings_manager.get_account_sort_by(),
            )
        )
        self._make_dropdown(
            frame,
            label="Sort accounts by",
            description=(
                "Controls the order account cards appear in the main menu."
            ),
            variable=self.sort_var,
            options=list(SORT_BY_OPTIONS.keys()),
        )

    # ------------------------------------------------------------------
    # Section: Master password change
    # ------------------------------------------------------------------
    def _build_master_password_section(self, parent):
        frame = self._make_section(parent, "Master Password")

        tk.Label(
            frame,
            text=(
                "Change the master password used to log in and encrypt your "
                "vault. Your vault will be re-encrypted with the new key."
            ),
            font=("Arial", 9),
            bg="#ffffff",
            fg="#666666",
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(2, 6))

        tk.Button(
            frame,
            text="Change Master Password...",
            command=self._open_change_password_dialog,
            font=("Arial", 11, "bold"),
            bg="#2196F3",
            fg="white",
            cursor="hand2",
            width=28,
        ).pack(anchor="w", padx=14, pady=(0, 10))

    # ------------------------------------------------------------------
    # Section: Vault (export/import)
    # ------------------------------------------------------------------
    def _build_vault_section(self, parent):
        frame = self._make_section(parent, "Vault")

        tk.Label(
            frame,
            text=(
                "Export your encrypted vault as a .zip (to your Downloads "
                "folder) to move it to another device, or import a previously "
                "exported vault."
            ),
            font=("Arial", 9),
            bg="#ffffff",
            fg="#666666",
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(2, 6))

        row = tk.Frame(frame, bg="#ffffff")
        row.pack(anchor="w", padx=14, pady=(0, 12))

        tk.Button(
            row,
            text="Export Vault...",
            command=self._on_export,
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            cursor="hand2",
            width=18,
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            row,
            text="Import Vault...",
            command=self._on_import,
            font=("Arial", 11, "bold"),
            bg="#FF9800",
            fg="white",
            cursor="hand2",
            width=18,
        ).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Section / dropdown builders
    # ------------------------------------------------------------------
    def _make_section(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg="#ffffff", relief=tk.RIDGE, borderwidth=1)
        outer.pack(fill=tk.X, pady=8, padx=2)

        tk.Label(
            outer,
            text=title,
            font=("Arial", 13, "bold"),
            bg="#ffffff",
            fg="#2196F3",
        ).pack(anchor="w", padx=14, pady=(10, 4))

        return outer

    def _make_dropdown(self, parent, *, label, description, variable, options):
        row = tk.Frame(parent, bg="#ffffff")
        row.pack(fill=tk.X, padx=14, pady=(4, 8))

        tk.Label(
            row,
            text=label,
            font=("Arial", 11, "bold"),
            bg="#ffffff",
        ).grid(row=0, column=0, sticky="w")

        combo = ttk.Combobox(
            row,
            textvariable=variable,
            values=options,
            state="readonly",
            width=22,
            font=("Arial", 10),
        )
        combo.grid(row=0, column=1, padx=(10, 0), sticky="e")

        row.columnconfigure(0, weight=1)

        tk.Label(
            parent,
            text=description,
            font=("Arial", 9),
            bg="#ffffff",
            fg="#666666",
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 8))

    # ------------------------------------------------------------------
    # Save handler
    # ------------------------------------------------------------------
    def _on_save(self):
        sm = self.settings_manager
        sm.set("auto_logout_time", AUTO_LOGOUT_OPTIONS[self.auto_logout_var.get()])
        sm.set("password_renewal_days", PASSWORD_RENEWAL_OPTIONS[self.renewal_var.get()])
        sm.set("clipboard_autoclear_seconds", CLIPBOARD_AUTOCLEAR_OPTIONS[self.clipboard_var.get()])
        sm.set("password_strength_requirement", PASSWORD_STRENGTH_OPTIONS[self.strength_var.get()])
        sm.set("account_sort_by", SORT_BY_OPTIONS[self.sort_var.get()])

        if sm.save():
            messagebox.showinfo(
                "Settings saved",
                "Settings saved. Note: auto-logout changes take effect on "
                "next login, all other settings apply immediately.",
                parent=self,
            )
            if self.callback:
                try:
                    self.callback()
                except Exception as e:
                    print(f"[settings] refresh callback failed: {e}")
        else:
            messagebox.showerror(
                "Error", "Failed to save settings.", parent=self
            )

    # ------------------------------------------------------------------
    # Change master password
    # ------------------------------------------------------------------
    def _open_change_password_dialog(self):
        ChangeMasterPasswordDialog(
            self,
            self.username,
            self.settings_manager,
            self.login_manager,
            on_success=self._on_master_password_changed,
        )

    def _on_master_password_changed(self, new_password):
        """
        Called after the master password has been successfully changed.
        Update the locally-cached master_password so export/import in the
        same session can continue to work.
        """
        self.master_password = new_password

        # Also update the AccountManager on the main menu side, since its
        # encryption key is derived from the old password.
        try:
            from services.account import AccountManager
            # Rebuild the main menu's account manager with the new password
            if self.master and hasattr(self.master, "account_manager"):
                self.master.account_manager = AccountManager(
                    self.username, new_password
                )
                self.master.master_password = new_password
        except Exception as e:
            print(f"[settings] Failed to update AccountManager in parent: {e}")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _on_export(self):
        if not self.master_password:
            messagebox.showerror(
                "Export",
                "Could not determine your master password for this session. "
                "Please log out and log in again.",
                parent=self,
            )
            return

        ok, result = self.settings_manager.export_vault(self.master_password)
        if ok:
            messagebox.showinfo(
                "Export complete",
                f"Vault exported to:\n\n{result}",
                parent=self,
            )
        else:
            messagebox.showerror("Export failed", result, parent=self)

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------
    def _on_import(self):
        if not self.master_password:
            messagebox.showerror(
                "Import",
                "Could not determine your master password for this session. "
                "Please log out and log in again.",
                parent=self,
            )
            return

        zip_path = filedialog.askopenfilename(
            parent=self,
            title="Select exported vault zip",
            filetypes=[("BlueVault export (*.zip)", "*.zip"), ("All files", "*.*")],
        )
        if not zip_path:
            return

        mode = self._ask_import_mode()
        if mode is None:
            return

        ok, msg = self.settings_manager.import_vault(
            zip_path, self.master_password, mode=mode
        )
        if ok:
            messagebox.showinfo("Import complete", msg, parent=self)
            if self.callback:
                try:
                    self.callback()
                except Exception as e:
                    print(f"[settings] refresh callback failed: {e}")
        else:
            messagebox.showerror("Import failed", msg, parent=self)

    def _ask_import_mode(self):
        """
        Small modal that asks the user whether to override or append.
        Returns "override", "append", or None (cancelled).
        """
        dlg = tk.Toplevel(self)
        dlg.title("Import mode")
        dlg.geometry("420x210")
        dlg.configure(bg="#f0f0f0")
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(
            dlg,
            text="How would you like to import?",
            font=("Arial", 13, "bold"),
            bg="#f0f0f0",
        ).pack(pady=(14, 4))

        tk.Label(
            dlg,
            text=(
                "Override: replace ALL current accounts with the imported "
                "ones.\n\nAppend: keep current accounts and add only new "
                "ones from the import (no duplicates)."
            ),
            font=("Arial", 9),
            bg="#f0f0f0",
            fg="#666666",
            wraplength=380,
            justify="left",
        ).pack(padx=14, pady=(0, 10))

        result = {"mode": None}

        def pick(mode):
            result["mode"] = mode
            dlg.destroy()

        btns = tk.Frame(dlg, bg="#f0f0f0")
        btns.pack(pady=(0, 10))

        tk.Button(
            btns,
            text="Override",
            command=lambda: pick("override"),
            font=("Arial", 11, "bold"),
            bg="#F44336",
            fg="white",
            width=12,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            btns,
            text="Append",
            command=lambda: pick("append"),
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            width=12,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            btns,
            text="Cancel",
            command=dlg.destroy,
            font=("Arial", 11),
            bg="#9E9E9E",
            fg="white",
            width=10,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)

        self.wait_window(dlg)
        return result["mode"]


# -----------------------------------------------------------------------------
# Change master password dialog
# -----------------------------------------------------------------------------
class ChangeMasterPasswordDialog(tk.Toplevel):
    def __init__(self, master, username, settings_manager, login_manager,
                 on_success=None):
        super().__init__(master)
        self.username = username
        self.settings_manager = settings_manager
        self.login_manager = login_manager
        self.on_success = on_success

        self.title("Change master password - BlueVault")
        self.geometry("460x380")
        self.configure(bg="#f0f0f0")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self,
            text="Change master password",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0",
        ).pack(pady=(16, 8))

        form = tk.Frame(self, bg="#f0f0f0")
        form.pack(pady=10)

        tk.Label(
            form,
            text="Current password:",
            font=("Arial", 11),
            bg="#f0f0f0",
        ).grid(row=0, column=0, sticky="e", padx=8, pady=6)
        self.current_entry = tk.Entry(form, font=("Arial", 11), width=26, show="*")
        self.current_entry.grid(row=0, column=1, padx=8, pady=6)

        tk.Label(
            form,
            text="New password:",
            font=("Arial", 11),
            bg="#f0f0f0",
        ).grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.new_entry = tk.Entry(form, font=("Arial", 11), width=26, show="*")
        self.new_entry.grid(row=1, column=1, padx=8, pady=6)

        tk.Label(
            form,
            text="Confirm new password:",
            font=("Arial", 11),
            bg="#f0f0f0",
        ).grid(row=2, column=0, sticky="e", padx=8, pady=6)
        self.confirm_entry = tk.Entry(form, font=("Arial", 11), width=26, show="*")
        self.confirm_entry.grid(row=2, column=1, padx=8, pady=6)

        # Show/hide toggle
        self.show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self,
            text="Show passwords",
            variable=self.show_var,
            command=self._toggle_show,
            font=("Arial", 10),
            bg="#f0f0f0",
        ).pack(pady=(2, 6))

        # Buttons
        btns = tk.Frame(self, bg="#f0f0f0")
        btns.pack(pady=10)

        tk.Button(
            btns,
            text="Change Password",
            command=self._on_confirm,
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            width=16,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            btns,
            text="Cancel",
            command=self.destroy,
            font=("Arial", 11),
            bg="#9E9E9E",
            fg="white",
            width=10,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=6)

        self.current_entry.focus()

    def _toggle_show(self):
        show = "" if self.show_var.get() else "*"
        for e in (self.current_entry, self.new_entry, self.confirm_entry):
            e.config(show=show)

    def _on_confirm(self):
        current = self.current_entry.get()
        new = self.new_entry.get()
        confirm = self.confirm_entry.get()

        ok, msg = self.settings_manager.change_master_password(
            self.login_manager, current, new, confirm
        )

        if ok:
            messagebox.showinfo("Success", msg, parent=self)
            if self.on_success:
                try:
                    self.on_success(new)
                except Exception as e:
                    print(f"[settings] on_success failed: {e}")
            self.destroy()
        else:
            messagebox.showerror("Change failed", msg, parent=self)


# For standalone testing
if __name__ == "__main__":
    from services.settings import SettingsManager
    from services.account import AccountManager
    from services.login import LoginManager

    root = tk.Tk()
    root.withdraw()

    username = "testuser"
    sm = SettingsManager(username)
    am = AccountManager(username, "testpass")
    lm = LoginManager()

    SettingsWindow(root, username, sm, am, lm, master_password="testpass")
    root.mainloop()
