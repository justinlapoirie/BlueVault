import tkinter as tk
from tkinter import messagebox
import sys
import os

# Ensure the parent directory is in sys.path so 'services' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui_controller import theme


class PasswordGeneratorApp(tk.Toplevel):
    """Password Generator as a Toplevel window that can be opened from main menu."""

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Password Generator - BlueVault")
        self.geometry("600x500")
        self.configure(bg=theme["app_bg"])

        # Import and create password generator instance with defaults
        from services.password_generator import PasswordGenerator
        self.password_generator = PasswordGenerator()

        # Persistent state across rebuilds (so a theme change doesn't
        # wipe the user's selections).
        self.length_var = tk.StringVar(master=self, value="12")
        self.uppercase_var = tk.BooleanVar(master=self, value=True)
        self.lowercase_var = tk.BooleanVar(master=self, value=True)
        self.digits_var = tk.BooleanVar(master=self, value=True)
        self.symbols_var = tk.BooleanVar(master=self, value=True)
        self.current_password = None

        self.create_widgets()

        # Theme integration
        theme.subscribe(self._apply_theme)
        self.bind("<Destroy>", self._on_destroy, add="+")

    # ------------------------------------------------------------------
    # Theme integration
    # ------------------------------------------------------------------
    def _apply_theme(self):
        try:
            for child in self.winfo_children():
                child.destroy()
            self.configure(bg=theme["app_bg"])
            self.create_widgets()
            # Restore previously generated password if there was one
            if self.current_password:
                self.password_label.config(text=self.current_password)
                self.copy_button.config(state=tk.NORMAL)
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
        tk.Label(
            self,
            text="Password Generator",
            font=("Segoe UI", 17, "bold"),
            bg=theme["app_bg"],
            fg=theme["accent"],
        ).pack(pady=16)

        tk.Frame(self, bg=theme["accent"], height=2).pack(fill=tk.X, padx=30)

        # Length row
        length_frame = tk.Frame(self, bg=theme["app_bg"])
        length_frame.pack(pady=14)

        tk.Label(
            length_frame,
            text="Password Length:",
            font=("Segoe UI", 11),
            bg=theme["app_bg"],
            fg=theme["text_primary"],
        ).pack(side=tk.LEFT, padx=5)

        length_entry = tk.Entry(
            length_frame,
            textvariable=self.length_var,
            font=("Segoe UI", 11),
            width=8,
            **theme.entry_style(),
        )
        length_entry.pack(side=tk.LEFT, padx=5)

        # Character type options
        options_frame = tk.LabelFrame(
            self,
            text="Character Types",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=10,
            **theme.labelframe_style(on="app_bg"),
        )
        options_frame.pack(pady=12, padx=30, fill=tk.BOTH)

        check_style = theme.checkbutton_style(on="app_bg")
        for text, var in (
            ("Uppercase  (A–Z)", self.uppercase_var),
            ("Lowercase  (a–z)", self.lowercase_var),
            ("Digits  (0–9)",    self.digits_var),
            ("Symbols  (!@#$…)", self.symbols_var),
        ):
            tk.Checkbutton(
                options_frame,
                text=text,
                variable=var,
                font=("Segoe UI", 10),
                **check_style,
            ).pack(anchor=tk.W, pady=3)

        # Generate button
        gen_style = theme.primary_button_style()
        gen_style.update(padx=24, pady=8)
        self.generate_button = tk.Button(
            self,
            text="Generate Password",
            command=self.on_button_click,
            **gen_style,
        )
        self.generate_button.pack(pady=14)

        # Password display
        pw_frame = tk.Frame(self, bg=theme["surface_bg"],
                            highlightbackground=theme["section_border"],
                            highlightthickness=1)
        pw_frame.pack(pady=6, padx=30, fill=tk.X)

        self.password_label = tk.Label(
            pw_frame,
            text="",
            font=("Consolas", 13, "bold"),
            bg=theme["surface_bg"],
            fg=theme["accent"],
            wraplength=380,
            justify=tk.CENTER,
            pady=12,
        )
        self.password_label.pack()

        # Copy button
        copy_style = theme.secondary_button_style()
        copy_style["font"] = ("Segoe UI", 10)
        self.copy_button = tk.Button(
            self,
            text="Copy to Clipboard",
            command=self.copy_to_clipboard,
            state=tk.DISABLED,
            **copy_style,
        )
        self.copy_button.pack(pady=8)


    def on_button_click(self):
        """Generate password using the class-based generator."""
        try:
            # Get length from entry field
            length = int(self.length_var.get())

            # Get checkbox values
            include_uppercase = self.uppercase_var.get()
            include_lowercase = self.lowercase_var.get()
            include_digits = self.digits_var.get()
            include_symbols = self.symbols_var.get()

            # Generate password using the class instance
            password = self.password_generator.generate_password(
                length=length,
                include_uppercase=include_uppercase,
                include_lowercase=include_lowercase,
                include_digits=include_digits,
                include_symbols=include_symbols,
            )

            # Display the generated password
            self.password_label.config(text=password)
            self.current_password = password
            self.copy_button.config(state=tk.NORMAL)

        except ValueError as e:
            messagebox.showerror("Error", str(e))
            self.password_label.config(text="")
            self.copy_button.config(state=tk.DISABLED)

    def copy_to_clipboard(self):
        """Copy the generated password to clipboard."""
        if self.current_password:
            self.clipboard_clear()
            self.clipboard_append(self.current_password)
            messagebox.showinfo("Copied", "Password copied to clipboard!")


# For standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = PasswordGeneratorApp()
    app.mainloop()
