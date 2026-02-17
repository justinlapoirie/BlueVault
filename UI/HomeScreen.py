import tkinter as tk
import sys
import os
# Ensure the parent directory is in sys.path so 'services' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blue Vault")
        self.geometry("400x300")
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self, text="Generate a random password", font=("Arial", 16))
        self.label.pack(pady=20)

        self.button = tk.Button(self, text="Generate", command=self.on_button_click)
        self.button.pack(pady=10)

    def on_button_click(self):
        from services.password_generator import generate_password
        password = generate_password(length=12, include_uppercase=True, include_lowercase=True, include_digits=True, include_symbols=True)
        self.label.config(text=f"Generated Password: {password}")        


if __name__ == "__main__":
    app = App()
    app.mainloop()