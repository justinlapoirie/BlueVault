"""
Settings window for BlueVault.

Opened from the main menu's gear button. Provides dropdowns for the
configurable settings (auto-logout, password renewal, clipboard auto-
clear, password strength requirement, account sorting, and appearance
theme), plus buttons for change master password, export vault, and
import vault.

All colors are pulled from :mod:`gui.ui_controller` so the window
respects the active light/dark theme and re-paints itself live when the
user toggles the theme.
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
from ui_controller import theme, position_bottom_right


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
        # Dock the settings dialog at the bottom-right of the screen
        # so it doesn't cover the user's vault content while they
        # tweak settings.
        position_bottom_right(self, 640, 780)
        self.configure(bg=theme["app_bg"])
        self.resizable(False, True)

        # Make modal-ish
        self.transient(master)
        self.grab_set()

        # Apply ttk styling so the comboboxes match the theme.
        theme.configure_ttk(self)

        self._build_ui()

        # Live-update on theme change.
        theme.subscribe(self._apply_theme)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self.bind("<Escape>", lambda e: self.destroy())

    # ------------------------------------------------------------------
    # Theme integration
    # ------------------------------------------------------------------
    def _apply_theme(self):
        try:
            self.configure(bg=theme["app_bg"])
            theme.configure_ttk(self)

            # Snapshot the user's in-progress (unsaved) selections so
            # they survive the rebuild.
            try:
                snapshot = {
                    "auto": self.auto_logout_var.get(),
                    "renewal": self.renewal_var.get(),
                    "clipboard": self.clipboard_var.get(),
                    "strength": self.strength_var.get(),
                    "sort": self.sort_var.get(),
                    "theme": self.theme_var.get(),
                }
            except (AttributeError, tk.TclError):
                snapshot = None

            for child in self.winfo_children():
                child.destroy()
            self._build_ui()

            if snapshot:
                try:
                    self.auto_logout_var.set(snapshot["auto"])
                    self.renewal_var.set(snapshot["renewal"])
                    self.clipboard_var.set(snapshot["clipboard"])
                    self.strength_var.set(snapshot["strength"])
                    self.sort_var.set(snapshot["sort"])
                    self.theme_var.set(snapshot["theme"])
                except (AttributeError, tk.TclError):
                    pass
        except tk.TclError:
            pass

    def _on_destroy(self, event):
        if event.widget is self:
            theme.unsubscribe(self._apply_theme)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Title
        tk.Label(
            self,
            text="Settings",
            font=("Segoe UI", 20, "bold"),
            bg=theme["app_bg"],
            fg=theme["accent"],
        ).pack(pady=(18, 6))

        tk.Label(
            self,
            text=f"Logged in as: {self.username}",
            font=("Segoe UI", 10, "italic"),
            bg=theme["app_bg"],
            fg=theme["text_secondary"],
        ).pack(pady=(0, 10))

        # Scrollable container so the window stays usable on smaller screens
        container = tk.Frame(self, bg=theme["app_bg"])
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        canvas = tk.Canvas(container, bg=theme["app_bg"], highlightthickness=0)
        scroll = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=theme["app_bg"])

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Enable mousewheel scrolling while cursor is inside the canvas area.
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Sections (Appearance first so the theme toggle is right at the top)
        self._build_appearance_section(inner)
        self._build_security_section(inner)
        self._build_organization_section(inner)
        self._build_master_password_section(inner)
        self._build_vault_section(inner)

        # Bottom action bar (always visible)
        action_bar = tk.Frame(self, bg=theme["app_bg"])
        action_bar.pack(fill=tk.X, padx=16, pady=(6, 16))

        save_style = theme.success_button_style()
        save_style.update(font=("Segoe UI", 12, "bold"), width=16)
        tk.Button(
            action_bar,
            text="Save Settings",
            command=self._on_save,
            **save_style,
        ).pack(side=tk.RIGHT, padx=(6, 0))

        close_style = theme.secondary_button_style()
        close_style.update(font=("Segoe UI", 12), width=10)
        tk.Button(
            action_bar,
            text="Close",
            command=self.destroy,
            **close_style,
        ).pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Section: Appearance (theme toggle)
    # ------------------------------------------------------------------
    def _build_appearance_section(self, parent):
        frame = self._make_section(parent, "Appearance")

        # Pull the live list of themes (built-ins + any imported by the
        # user) every time we (re)build the section so newly-imported
        # themes show up without needing a restart.
        options = theme.available_themes()  # {label: name}
        self._theme_options = options       # remember for _on_theme_var_changed

        self.theme_var = tk.StringVar(
            master=self,
            value=_label_for_value(options, theme.current_name),
        )

        # Wire a trace so the toggle applies immediately -- the user
        # doesn't have to hit Save before they see the change.
        self.theme_var.trace_add("write", self._on_theme_var_changed)

        self._make_dropdown(
            frame,
            label="Theme",
            description=(
                "Switch between built-in light/dark schemes or any theme "
                "you've imported. Changes apply to every BlueVault window "
                "immediately and are remembered across sessions."
            ),
            variable=self.theme_var,
            options=list(options.keys()),
        )



    def _on_theme_var_changed(self, *_args):
        try:
            label = self.theme_var.get()
        except tk.TclError:
            return
        options = getattr(self, "_theme_options", None) or theme.available_themes()
        new_theme = options.get(label)
        if not new_theme:
            return
        if new_theme == theme.current_name:
            return
        # set_theme persists via the attached SettingsManager and
        # notifies every subscribed window (including this one, which
        # rebuilds itself via _apply_theme).
        theme.set_theme(new_theme)

    # ------------------------------------------------------------------
    # Section: Security (auto-logout, renewal, clipboard, strength)
    # ------------------------------------------------------------------
    def _build_security_section(self, parent):
        frame = self._make_section(parent, "Security")

        # IMPORTANT: every StringVar passes ``master=self`` so it binds
        # to THIS Toplevel's Tk root (otherwise multi-root setups can
        # leave the variable unread by the combobox).

        # Auto-logout
        self.auto_logout_var = tk.StringVar(
            master=self,
            value=_label_for_value(
                AUTO_LOGOUT_OPTIONS,
                self.settings_manager.get_auto_logout_time(),
            ),
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
            master=self,
            value=_label_for_value(
                PASSWORD_RENEWAL_OPTIONS,
                self.settings_manager.get_password_renewal_days(),
            ),
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
            master=self,
            value=_label_for_value(
                CLIPBOARD_AUTOCLEAR_OPTIONS,
                self.settings_manager.get_clipboard_autoclear_seconds(),
            ),
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
            master=self,
            value=_label_for_value(
                PASSWORD_STRENGTH_OPTIONS,
                self.settings_manager.get_password_strength_requirement(),
            ),
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
            master=self,
            value=_label_for_value(
                SORT_BY_OPTIONS,
                self.settings_manager.get_account_sort_by(),
            ),
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
            font=("Segoe UI", 9),
            bg=theme["section_bg"],
            fg=theme["text_secondary"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(2, 6))

        change_style = theme.primary_button_style()
        change_style.update(font=("Segoe UI", 11, "bold"), width=28)
        tk.Button(
            frame,
            text="Change Master Password...",
            command=self._open_change_password_dialog,
            **change_style,
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
            font=("Segoe UI", 9),
            bg=theme["section_bg"],
            fg=theme["text_secondary"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(2, 6))

        row = tk.Frame(frame, bg=theme["section_bg"])
        row.pack(anchor="w", padx=14, pady=(0, 12))

        export_style = theme.success_button_style()
        export_style.update(font=("Segoe UI", 11, "bold"), width=18)
        tk.Button(
            row,
            text="Export Vault...",
            command=self._on_export,
            **export_style,
        ).pack(side=tk.LEFT, padx=(0, 10))

        import_style = theme.warn_button_style()
        import_style.update(font=("Segoe UI", 11, "bold"), width=18)
        tk.Button(
            row,
            text="Import Vault...",
            command=self._on_import,
            **import_style,
        ).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Section / dropdown builders
    # ------------------------------------------------------------------
    def _make_section(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(
            parent,
            bg=theme["section_bg"],
            relief=tk.RIDGE,
            borderwidth=1,
            highlightbackground=theme["section_border"],
        )
        outer.pack(fill=tk.X, pady=8, padx=2)

        tk.Label(
            outer,
            text=title,
            font=("Segoe UI", 13, "bold"),
            bg=theme["section_bg"],
            fg=theme["accent"],
        ).pack(anchor="w", padx=14, pady=(10, 4))

        return outer

    def _make_dropdown(self, parent, *, label, description, variable, options):
        section_bg = theme["section_bg"]

        row = tk.Frame(parent, bg=section_bg)
        row.pack(fill=tk.X, padx=14, pady=(4, 8))

        tk.Label(
            row,
            text=label,
            font=("Segoe UI", 11, "bold"),
            bg=section_bg,
            fg=theme["text_primary"],
        ).grid(row=0, column=0, sticky="w")

        combo = ttk.Combobox(
            row,
            textvariable=variable,
            values=options,
            state="readonly",
            width=22,
            font=("Segoe UI", 10),
            style="BlueVault.TCombobox",
        )
        combo.grid(row=0, column=1, padx=(10, 0), sticky="e")

        # Style the dropdown popup Listbox for dark mode. The popup is a
        # plain tk.Listbox that doesn't inherit ttk styles, so we patch
        # it via postcommand each time the dropdown opens.
        def _style_popup(c=combo):
            try:
                popup = c.tk.eval(f"ttk::combobox::PopdownWindow {c}")
                lb = c.nametowidget(popup + ".f.l")
                lb.configure(
                    background=theme["input_bg"],
                    foreground=theme["input_fg"],
                    selectbackground=theme["accent"],
                    selectforeground=theme["btn_primary_fg"],
                )
            except tk.TclError:
                pass
        combo.configure(postcommand=_style_popup)

        # Force the combobox to display the variable's current value.
        # Required because, on some Tk builds, a freshly-created Combobox
        # does not reliably mirror its textvariable's pre-existing value
        # until the user interacts with it.
        initial = variable.get()
        if initial in options:
            combo.set(initial)
        elif options:
            combo.set(options[0])
            variable.set(options[0])

        row.columnconfigure(0, weight=1)

        tk.Label(
            parent,
            text=description,
            font=("Segoe UI", 9),
            bg=section_bg,
            fg=theme["text_secondary"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 8))

    # ------------------------------------------------------------------
    # Save handler
    # ------------------------------------------------------------------
    def _on_save(self):
        sm = self.settings_manager

        # Defensive lookup helper -- if the StringVar somehow returned an
        # empty / unknown string, fall back to the currently-stored
        # setting value rather than raising KeyError (which used to abort
        # _on_save silently and leave the JSON file at defaults).
        def resolve(options, label, current):
            if label in options:
                return options[label]
            print(
                f"[settings] WARNING: dropdown returned unknown label "
                f"{label!r}; keeping current value {current!r}."
            )
            return current

        sm.set(
            "auto_logout_time",
            resolve(
                AUTO_LOGOUT_OPTIONS,
                self.auto_logout_var.get(),
                sm.get_auto_logout_time(),
            ),
        )
        sm.set(
            "password_renewal_days",
            resolve(
                PASSWORD_RENEWAL_OPTIONS,
                self.renewal_var.get(),
                sm.get_password_renewal_days(),
            ),
        )
        sm.set(
            "clipboard_autoclear_seconds",
            resolve(
                CLIPBOARD_AUTOCLEAR_OPTIONS,
                self.clipboard_var.get(),
                sm.get_clipboard_autoclear_seconds(),
            ),
        )
        sm.set(
            "password_strength_requirement",
            resolve(
                PASSWORD_STRENGTH_OPTIONS,
                self.strength_var.get(),
                sm.get_password_strength_requirement(),
            ),
        )
        sm.set(
            "account_sort_by",
            resolve(
                SORT_BY_OPTIONS,
                self.sort_var.get(),
                sm.get_account_sort_by(),
            ),
        )
        # Theme dropdown options are dynamic (built-ins + imports), so
        # build the lookup table on the fly.
        sm.set(
            "theme",
            resolve(
                theme.available_themes(),
                self.theme_var.get(),
                sm.get_theme(),
            ),
        )

        print(
            f"[settings] saving for {self.username}: "
            f"auto_logout={sm.get_auto_logout_time()}, "
            f"renewal={sm.get_password_renewal_days()}, "
            f"clipboard={sm.get_clipboard_autoclear_seconds()}, "
            f"strength={sm.get_password_strength_requirement()!r}, "
            f"sort={sm.get_account_sort_by()!r}, "
            f"theme={sm.get_theme()!r}"
        )

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
        dlg.configure(bg=theme["app_bg"])
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(
            dlg,
            text="How would you like to import?",
            font=("Segoe UI", 13, "bold"),
            bg=theme["app_bg"],
            fg=theme["text_primary"],
        ).pack(pady=(14, 4))

        tk.Label(
            dlg,
            text=(
                "Override: replace ALL current accounts with the imported "
                "ones.\n\nAppend: keep current accounts and add only new "
                "ones from the import (no duplicates)."
            ),
            font=("Segoe UI", 9),
            bg=theme["app_bg"],
            fg=theme["text_secondary"],
            wraplength=380,
            justify="left",
        ).pack(padx=14, pady=(0, 10))

        result = {"mode": None}

        def pick(mode):
            result["mode"] = mode
            dlg.destroy()

        btns = tk.Frame(dlg, bg=theme["app_bg"])
        btns.pack(pady=(0, 10))

        override_style = theme.danger_button_style()
        override_style.update(font=("Segoe UI", 11, "bold"), width=12)
        tk.Button(
            btns,
            text="Override",
            command=lambda: pick("override"),
            **override_style,
        ).pack(side=tk.LEFT, padx=6)

        append_style = theme.success_button_style()
        append_style.update(font=("Segoe UI", 11, "bold"), width=12)
        tk.Button(
            btns,
            text="Append",
            command=lambda: pick("append"),
            **append_style,
        ).pack(side=tk.LEFT, padx=6)

        cancel_style = theme.secondary_button_style()
        cancel_style.update(font=("Segoe UI", 11), width=10)
        tk.Button(
            btns,
            text="Cancel",
            command=dlg.destroy,
            **cancel_style,
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
        self.configure(bg=theme["app_bg"])
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self,
            text="Change master password",
            font=("Segoe UI", 16, "bold"),
            bg=theme["app_bg"],
            fg=theme["accent"],
        ).pack(pady=(16, 8))

        form = tk.Frame(self, bg=theme["app_bg"])
        form.pack(pady=10)

        def add_row(row, text, entry_attr):
            tk.Label(
                form,
                text=text,
                font=("Segoe UI", 11),
                bg=theme["app_bg"],
                fg=theme["text_primary"],
            ).grid(row=row, column=0, sticky="e", padx=8, pady=6)
            entry = tk.Entry(form, font=("Segoe UI", 11), width=26, show="*",
                             **theme.entry_style())
            entry.grid(row=row, column=1, padx=8, pady=6)
            setattr(self, entry_attr, entry)

        add_row(0, "Current password:", "current_entry")
        add_row(1, "New password:", "new_entry")
        add_row(2, "Confirm new password:", "confirm_entry")

        self.show_var = tk.BooleanVar(master=self, value=False)
        tk.Checkbutton(
            self,
            text="Show passwords",
            variable=self.show_var,
            command=self._toggle_show,
            font=("Segoe UI", 10),
            **theme.checkbutton_style(on="app_bg"),
        ).pack(pady=(2, 6))

        btns = tk.Frame(self, bg=theme["app_bg"])
        btns.pack(pady=10)

        change_style = theme.success_button_style()
        change_style.update(font=("Segoe UI", 11, "bold"), width=16)
        tk.Button(btns, text="Change Password", command=self._on_confirm,
                  **change_style).pack(side=tk.LEFT, padx=6)

        cancel_style = theme.secondary_button_style()
        cancel_style.update(font=("Segoe UI", 11), width=10)
        tk.Button(btns, text="Cancel", command=self.destroy,
                  **cancel_style).pack(side=tk.LEFT, padx=6)

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
