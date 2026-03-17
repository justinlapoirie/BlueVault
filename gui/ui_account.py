import tkinter as tk
from tkinter import messagebox
import sys
import os

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class AccountWindow(tk.Toplevel):
    """Window for creating or editing password vault accounts."""

    def __init__(self, master, account_manager, mode="create", account_data=None, callback=None):
        """
        Initialize the account window.

        Args:
            master: Parent window
            account_manager: AccountManager instance
            mode: "create" or "edit"
            account_data: Existing account data (for edit mode)
            callback: Function to call after save
        """
        super().__init__(master)

        self.account_manager = account_manager
        self.mode = mode
        self.account_data = account_data
        self.callback = callback

        # Window configuration
        if mode == "create":
            self.title("New Account - BlueVault")
        else:
            self.title("Edit Account - BlueVault")

        self.geometry("500x550")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")

        # Make window modal
        self.transient(master)
        self.grab_set()

        self.create_widgets()

        # Populate fields if editing
        if mode == "edit" and account_data:
            self.populate_fields(account_data)

    def create_widgets(self):
        """Create all form widgets."""
        # Title
        title_text = "Create New Account" if self.mode == "create" else "Edit Account"
        tk.Label(
            self,
            text=title_text,
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        ).pack(pady=20)

        # Form frame
        form_frame = tk.Frame(self, bg="#f0f0f0")
        form_frame.pack(pady=10, padx=40, fill=tk.BOTH, expand=True)

        # Account Name (Required)
        tk.Label(
            form_frame,
            text="Account Name: *",
            font=("Arial", 11, "bold"),
            bg="#f0f0f0",
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.account_name_entry = tk.Entry(form_frame, font=("Arial", 11), width=40)
        self.account_name_entry.grid(row=1, column=0, pady=(0, 15))
        self.account_name_entry.focus()

        # Username (Required)
        tk.Label(
            form_frame,
            text="Username/Email: *",
            font=("Arial", 11, "bold"),
            bg="#f0f0f0",
            anchor="w"
        ).grid(row=2, column=0, sticky="w", pady=(0, 5))

        self.username_entry = tk.Entry(form_frame, font=("Arial", 11), width=40)
        self.username_entry.grid(row=3, column=0, pady=(0, 15))

        # Password (Required)
        password_label_frame = tk.Frame(form_frame, bg="#f0f0f0")
        password_label_frame.grid(row=4, column=0, sticky="w", pady=(0, 5))

        tk.Label(
            password_label_frame,
            text="Password: *",
            font=("Arial", 11, "bold"),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT)

        # Password entry with show/hide and generate button
        password_container = tk.Frame(form_frame, bg="#f0f0f0")
        password_container.grid(row=5, column=0, pady=(0, 15))

        # Create Entry first
        self.password_entry = tk.Entry(
            password_container,
            font=("Arial", 11),
            width=26,
            show="*"
        )
        self.password_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Generate password button
        tk.Button(
            password_container,
            text="🔑 Generate",
            command=self.generate_password,
            font=("Arial", 9),
            bg="#4CAF50",
            fg="white",
            cursor="hand2",
            relief=tk.RAISED,
            padx=5
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Show/hide checkbox - initialize BooleanVar and create checkbutton
        self.show_password_var = tk.BooleanVar(value=False)
        self.show_password_checkbox = tk.Checkbutton(
            password_container,
            text="Show",
            variable=self.show_password_var,
            command=self.toggle_password,
            font=("Arial", 9),
            bg="#f0f0f0"
        )
        self.show_password_checkbox.pack(side=tk.LEFT)

        # Website URL (Optional)
        tk.Label(
            form_frame,
            text="Website URL: (optional)",
            font=("Arial", 11),
            bg="#f0f0f0",
            anchor="w"
        ).grid(row=6, column=0, sticky="w", pady=(0, 5))

        self.website_entry = tk.Entry(form_frame, font=("Arial", 11), width=40)
        self.website_entry.grid(row=7, column=0, pady=(0, 15))

        # Notes (Optional)
        tk.Label(
            form_frame,
            text="Notes: (optional)",
            font=("Arial", 11),
            bg="#f0f0f0",
            anchor="w"
        ).grid(row=8, column=0, sticky="w", pady=(0, 5))

        self.notes_text = tk.Text(
            form_frame,
            font=("Arial", 10),
            width=40,
            height=5,
            wrap=tk.WORD
        )
        self.notes_text.grid(row=9, column=0, pady=(0, 15))

        # Required fields note
        tk.Label(
            form_frame,
            text="* Required fields",
            font=("Arial", 9, "italic"),
            bg="#f0f0f0",
            fg="#666666"
        ).grid(row=10, column=0, sticky="w")

        # Buttons frame
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="Save",
            command=self.save_account,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=12,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            font=("Arial", 12),
            bg="#9E9E9E",
            fg="white",
            width=12,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

    def toggle_password(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
        # Force widget update to ensure visibility change takes effect
        self.password_entry.update_idletasks()

    def generate_password(self):
        """Generate a password with default parameters and insert into field."""
        try:
            from services.password_generator import PasswordGenerator

            # Create generator with default parameters
            generator = PasswordGenerator(
                length=12,
                include_uppercase=True,
                include_lowercase=True,
                include_digits=True,
                include_symbols=True
            )

            # Generate password
            password = generator.generate_password()

            # Clear current password and insert generated one
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, password)

            # Briefly show the password so user can see it was generated
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

        # Save account
        try:
            if self.mode == "create":
                result = self.account_manager.create_account(
                    account_name=account_name,
                    username=username,
                    password=password,
                    notes=notes,
                    website_url=website_url
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
                    website_url=website_url
                )

                if result:
                    messagebox.showinfo("Success", "Account updated successfully!")
                else:
                    messagebox.showerror("Error", "Failed to update account.")
                    return

            # Call callback to refresh main menu
            if self.callback:
                self.callback()

            # Close window
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")


# For standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    # Import account manager
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from services.account import AccountManager

    manager = AccountManager("testuser", "testpass")

    app = AccountWindow(root, manager, mode="create")
    app.mainloop()