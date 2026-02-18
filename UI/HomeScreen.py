import tkinter as tk
from tkinter import messagebox
import sys
import os

# Ensure the parent directory is in sys.path so 'services' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blue Vault")
        self.geometry("600x500")
        
        # Import and create password generator instance with defaults
        from services.password_generator import PasswordGenerator
        self.password_generator = PasswordGenerator()
        
        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self, text="Password Generator", font=("Arial", 18, "bold")
        )
        title_label.pack(pady=20)

        # Frame for password length
        length_frame = tk.Frame(self)
        length_frame.pack(pady=10)

        tk.Label(length_frame, text="Password Length:", font=("Arial", 11)).pack(
            side=tk.LEFT, padx=5
        )
        self.length_var = tk.StringVar(value="12")
        length_entry = tk.Entry(length_frame, textvariable=self.length_var, width=10)
        length_entry.pack(side=tk.LEFT, padx=5)

        # Frame for character type options
        options_frame = tk.LabelFrame(
            self, text="Include Character Types", font=("Arial", 11), padx=20, pady=10
        )
        options_frame.pack(pady=15, padx=20, fill=tk.BOTH)

        self.uppercase_var = tk.BooleanVar(value=True)
        self.lowercase_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)

        #Checkbox for uppercase
        tk.Checkbutton(
            options_frame,
            text="Uppercase (A-Z)",
            variable=self.uppercase_var,
            font=("Arial", 10),
        ).pack(anchor=tk.W, pady=2)

        #Checkbox for lowercase
        tk.Checkbutton(
            options_frame,
            text="Lowercase (a-z)",
            variable=self.lowercase_var,
            font=("Arial", 10),
        ).pack(anchor=tk.W, pady=2)

        #Checkbox for numbers
        tk.Checkbutton(
            options_frame,
            text="Digits (0-9)",
            variable=self.digits_var,
            font=("Arial", 10),
        ).pack(anchor=tk.W, pady=2)

        #Checkbox for symbols
        tk.Checkbutton(
            options_frame,
            text="Symbols (!@#$...)",
            variable=self.symbols_var,
            font=("Arial", 10),
        ).pack(anchor=tk.W, pady=2)

        # Generate button
        self.generate_button = tk.Button(
            self,
            text="Generate Password",
            command=self.on_button_click,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
        )
        self.generate_button.pack(pady=15)

        # Frame for displaying password
        password_frame = tk.Frame(self)
        password_frame.pack(pady=10, padx=20, fill=tk.BOTH)

        self.password_label = tk.Label(
            password_frame,
            text="",
            font=("Courier", 12, "bold"),
            fg="#2196F3",
            wraplength=400,
            justify=tk.CENTER,
        )
        self.password_label.pack(pady=10)

        # Copy button
        self.copy_button = tk.Button(
            password_frame,
            text="Copy to Clipboard",
            command=self.copy_to_clipboard,
            font=("Arial", 10)
        )
        self.copy_button.pack(pady=5)

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
        if hasattr(self, "current_password"):
            self.clipboard_clear()
            self.clipboard_append(self.current_password)
            messagebox.showinfo("Copied", "Password copied to clipboard!")


if __name__ == "__main__":
    app = App()
    app.mainloop()
