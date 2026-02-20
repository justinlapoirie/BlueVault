import tkinter as tk
from tkinter import messagebox, scrolledtext
import sys
import os

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class PasswordAuditorApp(tk.Toplevel):
    """Password Auditor as a Toplevel window that analyzes password strength."""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Password Auditor - BlueVault")
        self.geometry("550x600")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        
        # Import and create password auditor instance
        from services.password_auditor import PasswordAuditor
        self.password_auditor = PasswordAuditor()
        
        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self, 
            text="Password Auditor", 
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(pady=20)

        # Instructions
        instructions = tk.Label(
            self,
            text="Enter or paste a password to check its security",
            font=("Arial", 11),
            bg="#f0f0f0",
            fg="#666666"
        )
        instructions.pack(pady=5)

        # Frame for password input
        input_frame = tk.LabelFrame(
            self, 
            text="Password to Audit", 
            font=("Arial", 11, "bold"),
            bg="#f0f0f0",
            padx=20, 
            pady=15
        )
        input_frame.pack(pady=15, padx=20, fill=tk.BOTH)

        # Password entry with show/hide toggle
        entry_container = tk.Frame(input_frame, bg="#f0f0f0")
        entry_container.pack(fill=tk.X)

        self.password_entry = tk.Entry(
            entry_container, 
            font=("Courier", 12),
            width=35,
            show="*"
        )
        self.password_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.password_entry.focus()

        # Toggle visibility button
        self.show_password_var = tk.BooleanVar(value=False)
        self.toggle_button = tk.Checkbutton(
            entry_container,
            text="Show",
            variable=self.show_password_var,
            command=self.toggle_password_visibility,
            font=("Arial", 9),
            bg="#f0f0f0"
        )
        self.toggle_button.pack(side=tk.LEFT)

        # Bind Enter key to audit
        self.password_entry.bind("<Return>", lambda e: self.audit_password())

        # Audit button
        self.audit_button = tk.Button(
            self,
            text="Audit Password",
            command=self.audit_password,
            font=("Arial", 12, "bold"),
            bg="#FF9800",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.audit_button.pack(pady=15)

        # Results frame
        results_frame = tk.LabelFrame(
            self,
            text="Security Analysis",
            font=("Arial", 11, "bold"),
            bg="#f0f0f0",
            padx=20,
            pady=15
        )
        results_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Score display
        score_container = tk.Frame(results_frame, bg="#f0f0f0")
        score_container.pack(fill=tk.X, pady=5)

        tk.Label(
            score_container,
            text="Strength:",
            font=("Arial", 11, "bold"),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT)

        self.score_label = tk.Label(
            score_container,
            text="—",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0",
            fg="#666666"
        )
        self.score_label.pack(side=tk.LEFT, padx=10)

        # Entropy display
        entropy_container = tk.Frame(results_frame, bg="#f0f0f0")
        entropy_container.pack(fill=tk.X, pady=5)

        tk.Label(
            entropy_container,
            text="Entropy:",
            font=("Arial", 11),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT)

        self.entropy_label = tk.Label(
            entropy_container,
            text="—",
            font=("Arial", 11),
            bg="#f0f0f0",
            fg="#666666"
        )
        self.entropy_label.pack(side=tk.LEFT, padx=10)

        # Breached status
        self.breached_label = tk.Label(
            results_frame,
            text="",
            font=("Arial", 11, "bold"),
            bg="#f0f0f0"
        )
        self.breached_label.pack(pady=10)

        # Warnings display (scrollable)
        tk.Label(
            results_frame,
            text="Warnings & Recommendations:",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0"
        ).pack(anchor="w", pady=(10, 5))

        self.warnings_text = scrolledtext.ScrolledText(
            results_frame,
            font=("Arial", 10),
            height=8,
            width=50,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#ffffff"
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
            self.display_results(report)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during audit:\n{str(e)}")

    def display_results(self, report):
        """Display the audit results in the GUI."""
        # Display score with color coding
        score = report["score"]
        score_colors = {
            "Weak": "#F44336",      # Red
            "Moderate": "#FF9800",  # Orange
            "Strong": "#4CAF50"     # Green
        }
        
        self.score_label.config(
            text=score,
            fg=score_colors.get(score, "#666666")
        )

        # Display entropy
        entropy = report["entropy"]
        self.entropy_label.config(
            text=f"{entropy:.2f} bits"
        )

        # Display breached status
        if report["breached"]:
            self.breached_label.config(
                text="⚠️ PASSWORD FOUND IN DATA BREACH ⚠️",
                fg="#F44336"
            )
        else:
            self.breached_label.config(
                text="✓ Not found in known breaches",
                fg="#4CAF50"
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
    root.withdraw()  # Hide the root window
    app = PasswordAuditorApp()
    app.mainloop()
