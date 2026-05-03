import tkinter as tk
from tkinter import messagebox, scrolledtext
import sys
import os

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui_controller import theme


class PasswordAuditorApp(tk.Toplevel):
    """Password Auditor as a Toplevel window that analyzes password strength."""

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Password Auditor - BlueVault")
        self.geometry("550x600")
        self.configure(bg=theme["app_bg"])

        # Import and create password auditor instance
        from services.password_auditor import PasswordAuditor
        self.password_auditor = PasswordAuditor()

        # Persistent state
        self.show_password_var = tk.BooleanVar(master=self, value=False)
        self._last_report = None

        self.create_widgets()

        # Theme integration
        theme.subscribe(self._apply_theme)
        self.bind("<Destroy>", self._on_destroy, add="+")

    # ------------------------------------------------------------------
    # Theme integration
    # ------------------------------------------------------------------
    def _apply_theme(self):
        try:
            saved_password = self.password_entry.get() if hasattr(self, "password_entry") else ""
            for child in self.winfo_children():
                child.destroy()
            self.configure(bg=theme["app_bg"])
            self.create_widgets()
            if saved_password:
                self.password_entry.insert(0, saved_password)
            if self._last_report:
                self.display_results(self._last_report)
        except tk.TclError:
            pass

    def _on_destroy(self, event):
        if event.widget is self:
            theme.unsubscribe(self._apply_theme)

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------
    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self,
            text="Password Auditor",
            font=("Arial", 18, "bold"),
            bg=theme["app_bg"],
            fg=theme["accent"],
        )
        title_label.pack(pady=16)

        # Instructions
        instructions = tk.Label(
            self,
            text="Enter or paste a password to check its security",
            font=("Arial", 11),
            bg=theme["app_bg"],
            fg=theme["text_secondary"],
        )
        instructions.pack(pady=5)

        # Frame for password input
        input_frame = tk.LabelFrame(
            self,
            text="Password to Audit",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15,
            **theme.labelframe_style(on="app_bg"),
        )
        input_frame.pack(pady=15, padx=20, fill=tk.BOTH)

        # Password entry with show/hide toggle
        entry_container = tk.Frame(input_frame, bg=theme["app_bg"])
        entry_container.pack(fill=tk.X)

        self.password_entry = tk.Entry(
            entry_container,
            font=("Courier", 12),
            width=35,
            show="*",
            **theme.entry_style(),
        )
        self.password_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.password_entry.focus()

        # Toggle visibility button
        self.toggle_button = tk.Checkbutton(
            entry_container,
            text="Show",
            variable=self.show_password_var,
            command=self.toggle_password_visibility,
            font=("Arial", 9),
            **theme.checkbutton_style(on="app_bg"),
        )
        self.toggle_button.pack(side=tk.LEFT)

        # Bind Enter key to audit
        self.password_entry.bind("<Return>", lambda e: self.audit_password())

        # Audit button
        audit_style = theme.primary_button_style()
        audit_style.update(padx=20, pady=10)
        self.audit_button = tk.Button(
            self,
            text="Audit Password",
            command=self.audit_password,
            **audit_style,
        )
        self.audit_button.pack(pady=15)

        # Results frame
        results_bg = theme["surface_bg"]
        results_fg = theme["text_primary"]
        results_frame = tk.LabelFrame(
            self,
            text="Security Analysis",
            font=("Arial", 11, "bold"),
            bg=results_bg,
            fg=results_fg,
            padx=20,
            pady=15,
            highlightbackground=theme["section_border"],
        )
        results_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Score display
        score_container = tk.Frame(results_frame, bg=results_bg)
        score_container.pack(fill=tk.X, pady=5)

        tk.Label(
            score_container,
            text="Strength:",
            font=("Arial", 11, "bold"),
            bg=results_bg,
            fg=results_fg,
        ).pack(side=tk.LEFT)

        self.score_label = tk.Label(
            score_container,
            text="—",
            font=("Arial", 14, "bold"),
            bg=results_bg,
            fg=theme["status_neutral"],
        )
        self.score_label.pack(side=tk.LEFT, padx=10)

        # Entropy display
        entropy_container = tk.Frame(results_frame, bg=results_bg)
        entropy_container.pack(fill=tk.X, pady=5)

        tk.Label(
            entropy_container,
            text="Entropy:",
            font=("Arial", 11),
            bg=results_bg,
            fg=results_fg,
        ).pack(side=tk.LEFT)

        self.entropy_label = tk.Label(
            entropy_container,
            text="—",
            font=("Arial", 11),
            bg=results_bg,
            fg=theme["status_neutral"],
        )
        self.entropy_label.pack(side=tk.LEFT, padx=10)

        # Breached status
        self.breached_label = tk.Label(
            results_frame,
            text="",
            font=("Arial", 11, "bold"),
            bg=results_bg,
            fg=results_fg,
        )
        self.breached_label.pack(pady=10)

        # Warnings display (scrollable)
        tk.Label(
            results_frame,
            text="Warnings & Recommendations:",
            font=("Arial", 10, "bold"),
            bg=results_bg,
            fg=results_fg,
        ).pack(anchor="w", pady=(10, 5))

        self.warnings_text = scrolledtext.ScrolledText(
            results_frame,
            font=("Arial", 10),
            height=8,
            width=50,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=theme["surface_bg"],
            fg=theme["text_primary"],
            insertbackground=theme["input_caret"],
            relief=tk.FLAT,
        )
        self.warnings_text.pack(fill=tk.BOTH, expand=True)

    def toggle_password_visibility(self):
        """Toggle between showing and hiding the password."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def audit_password(self):
        """Audit the entered password and display results."""
        password = self.password_entry.get()

        if not password:
            messagebox.showwarning("No Password", "Please enter a password to audit.")
            return

        # Get audit results
        try:
            report = self.password_auditor.audit_password(password)
            self._last_report = report
            self.display_results(report)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during audit:\n{str(e)}")

    def display_results(self, report):
        """Display the audit results in the GUI."""
        # Display score with color coding
        score = report["score"]
        score_colors = {
            "Weak":     theme["score_weak"],
            "Moderate": theme["score_moderate"],
            "Strong":   theme["score_strong"],
        }

        self.score_label.config(
            text=score,
            fg=score_colors.get(score, theme["status_neutral"]),
        )

        # Display entropy
        entropy = report["entropy"]
        self.entropy_label.config(text=f"{entropy:.2f} bits")

        # Display breached status
        if report["breached"]:
            self.breached_label.config(
                text="⚠️ PASSWORD FOUND IN DATA BREACH ⚠️",
                fg=theme["status_danger"],
            )
        else:
            self.breached_label.config(
                text="✓ Not found in known breaches",
                fg=theme["status_success"],
            )

        # Display warnings
        self.warnings_text.config(state=tk.NORMAL)
        self.warnings_text.delete(1.0, tk.END)

        if report["warnings"]:
            for i, warning in enumerate(report["warnings"], 1):
                self.warnings_text.insert(tk.END, f"{i}. {warning}\n\n")
        else:
            self.warnings_text.insert(tk.END, "No warnings. This is a strong password!")

        self.warnings_text.config(state=tk.DISABLED)


# For standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = PasswordAuditorApp()
    app.mainloop()
