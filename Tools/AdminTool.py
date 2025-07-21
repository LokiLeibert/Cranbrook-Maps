# Route Finder Mobile
# UserRegistration.py
# 14 July 2025

# Allows registration of users and editing of available maps

import tkinter as tk
from tkinter import messagebox, filedialog, Listbox
from PIL import ImageTk, Image
from pysqlcipher3 import dbapi2 as sqlite
import bcrypt
import os

# Database setup
USER_DATABASE = "../users.db"
MAP_DIR = "../../maps"
ASSET_DIR = "../ui_components"
SECURE_KEY = "Loki"

if not os.path.exists(MAP_DIR):
    os.mkdir(MAP_DIR)


# Function to hash and salt a password
def hash_password(password):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed_password

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password)

# Initialize the database
def init_db():
    conn = sqlite.connect(USER_DATABASE)
    conn.execute(f"PRAGMA key = '{SECURE_KEY}';")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        privilege TEXT NOT NULL DEFAULT 'user'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_maps (
        user_id INTEGER NOT NULL,
        map_file TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_history (
        user_id INTEGER NOT NULL,
        history TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id))
    """)
    conn.commit()
    conn.close()



# Class for the main application
class AdminToolApp:
    def __init__(self, _root):

        # Font
        self.big_font = ("Helvetica", 24)
        self.font = ("Helvetica", 18)

        # Window Geometry
        self.frame = 400, 785

        # Configure main window and canvas
        self.root = _root
        self.root.title("Map Manager Login")
        self.root.geometry(f"{self.frame[0]}x{self.frame[1]}")

        # Frame overlay
        self.frame_image = Image.open(f"{ASSET_DIR}/frame.png")
        self.frame_image = self.frame_image.resize(self.frame, Image.Resampling.LANCZOS)
        self.frame_photo = ImageTk.PhotoImage(self.frame_image)

        # Elements used across screens
        self.username_entry = None
        self.password_entry = None
        self.map_listbox = None

        # Login page
        self.current_user_id = None
        self.username_entry = None
        self.setup_login_page()

    def setup_login_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, image=self.frame_photo).place(x=0, y=0, anchor="nw")

        tk.Label(self.root, text="Admin Login", font=self.big_font).place(x=200, y=50, anchor="center")
        tk.Label(self.root, text="Username", font=self.font).place(x=200, y=150, anchor="center")
        self.username_entry = tk.Entry(self.root, width=30, font=self.font)
        self.username_entry.place(x=200, y=190, anchor="center")

        tk.Label(self.root, text="Password", font=self.font).place(x=200, y=250, anchor="center")
        self.password_entry = tk.Entry(self.root, show="*", width=30, font=self.font)
        self.password_entry.place(x=200, y=290, anchor="center")

        tk.Button(
            self.root,
            text="Login",
            command=self.login,
            font=self.font
        ).place(x=150, y=500, anchor="nw")

    def setup_registration_page(self):
        if self.username_entry is not None:
            username = self.username_entry.get()
        else:
            username = ""

        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, image=self.frame_photo).place(x=0, y=0, anchor="nw")

        tk.Label(self.root, text="Register", font=self.big_font).place(x=200, y=50, anchor="center")
        tk.Label(self.root, text="Username", font=self.font).place(x=200, y=150, anchor="center")
        var = tk.StringVar(value=username)
        self.username_entry = tk.Entry(self.root, width=30, font=self.font, textvariable=var)
        self.username_entry.place(x=200, y=190, anchor="center")

        tk.Label(self.root, text="Password", font=self.font).place(x=200, y=250, anchor="center")
        self.password_entry = tk.Entry(self.root, show="*", width=30, font=self.font)
        self.password_entry.place(x=200, y=290, anchor="center")


        tk.Button(
            self.root,
            text="Register",
            command=self.register,
            font=self.font
        ).place(x=50, y=500, anchor="nw")
        tk.Button(
            self.root,
            text="Return to Login",
            command=self.setup_login_page,
            font=self.font
        ).place(x=200, y=500, anchor="nw")

        if len(username) > 0:
            self.password_entry.focus()
        else:
            self.username_entry.focus()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        conn = sqlite.connect(USER_DATABASE)
        conn.execute(f"PRAGMA key = '{SECURE_KEY}';")
        cursor = conn.cursor()

        cursor.execute("SELECT id, password, privilege FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result:
            user_id, hashed_password, privilege = result
            if verify_password(password, hashed_password) and privilege == 'admin':
                self.current_user_id = user_id
                self.setup_registration_page()
            else:
                messagebox.showerror("Error", "Invalid credentials.", parent=self.root)
        else:
            messagebox.showerror("Error", "Invalid credentials.", parent=self.root)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        hashed_password = hash_password(password)

        conn = sqlite.connect(USER_DATABASE)
        conn.execute(f"PRAGMA key = '{SECURE_KEY}';")
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                           (username, hashed_password))
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            user_id = result[0]
            cursor.execute("INSERT INTO user_maps (user_id, map_file) VALUES (?, ?)",
                           (user_id, "2023-SS-Campus-Map.rfo"))
            conn.commit()
            messagebox.showinfo("Success", "Account created! Please log in.")
            self.setup_login_page()
        except sqlite.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")
        finally:
            conn.close()

    def setup_main_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, image=self.frame_photo).place(x=0, y=0, anchor="nw")

        tk.Label(self.root, text="Select Map", font=self.big_font).place(x=200, y=50, anchor="center")

        self.map_listbox = Listbox(self.root, width=30, height=25, font=self.font)
        self.map_listbox.place(x=200, y=80, anchor="n")
        self.load_user_maps()

        tk.Button(self.root, text="Add Maps", command=self.add_maps).place(x=200, y=650, anchor="center")
        tk.Button(self.root, text="Remove Selected Map", command=self.remove_selected_map).place(x=200, y=680, anchor="center")
        tk.Button(self.root, text="Launch RouteFinder", command=self.launch_route_finder).place(x=200, y=710, anchor="center")
        tk.Button(self.root, text="Logout", command=self.logout).place(x=200, y=740, anchor="center")
        self.map_listbox.focus()

    def load_user_maps(self):
        self.map_listbox.delete(0, tk.END)
        conn = sqlite.connect(USER_DATABASE)
        conn.execute(f"PRAGMA key = '{SECURE_KEY}';")
        cursor = conn.cursor()
        cursor.execute("SELECT map_file FROM user_maps WHERE user_id = ?", (self.current_user_id,))
        maps = cursor.fetchall()
        conn.close()

        for map_file in maps:
            self.map_listbox.insert(tk.END, map_file[0])

    def add_maps(self):
        file_paths = filedialog.askopenfilenames(initialdir=MAP_DIR, title="Select Map Files",
                                                 filetypes=(("Route Finder Maps", "*.rfo"), ("All Files", "*.*")))
        conn = sqlite.connect(USER_DATABASE)
        conn.execute(f"PRAGMA key = '{SECURE_KEY}';")
        cursor = conn.cursor()

        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            cursor.execute("INSERT INTO user_maps (user_id, map_file) VALUES (?, ?)",
                           (self.current_user_id, file_name))
            if not os.path.exists(os.path.join(MAP_DIR, file_name)):
                os.rename(file_path, os.path.join(MAP_DIR, file_name))

        conn.commit()
        conn.close()
        self.load_user_maps()

    def remove_selected_map(self):
        selected = self.map_listbox.curselection()
        if selected:
            map_file = self.map_listbox.get(selected[0])
            conn = sqlite.connect(USER_DATABASE)
            conn.execute(f"PRAGMA key = '{SECURE_KEY}';")
            cursor = conn.cursor()

            cursor.execute("DELETE FROM user_maps WHERE user_id = ? AND map_file = ?",
                           (self.current_user_id, map_file))
            conn.commit()
            conn.close()

            self.load_user_maps()

    def launch_route_finder(self):
        selected = self.map_listbox.curselection()
        if selected:
            map_file = self.map_listbox.get(selected[0])
            print("Launch Route Finder with map:", map_file)
            self.root.destroy()
            self.root = None
            quit()
        else:
            messagebox.showerror("Error", "No map selected.")

    def logout(self):
        self.current_user_id = None
        self.setup_login_page()


# Main Execution
if __name__ == "__main__":
    init_db()

    root = tk.Tk()
    app = AdminToolApp(root)
    root.mainloop()
