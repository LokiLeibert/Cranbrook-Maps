# Route Finder Mobile
# Login.py
# 14 July 2025

# Creates a sqlite database: users.db containing three tables:
# 1. users table contains id, username and password (hashed and salted)
# 2. user_maps table containing the .rfo map files available to the user
# 3. user_history table containing last 5 locations looked up on the last session

# Security is provided by encrypting passwords using the Python bcrypt
# library that uses the blowfish cypher. It is ideal for password protection
# because it is computationally very costly
# so that a brute force attack is difficult.
# In addition, the hash_password function asks it to produce a salt string
# to add to the password to make it very difficult to use attacks based on
# password guessing.
# The blowfish hash does not make it possible to reconstruct passwords from the
# hash value, so that an attacker cannot use the database to generate passwords.
# Instead, we have a verify function that checks that the password entered is a
# match to the hashed and salted value stored in the database.


import tkinter as tk
from PIL import ImageTk, Image
import sqlite3
import bcrypt
import json
import os


# Database setup
USER_DATABASE = "users.db"
MAP_DIR = "maps"

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
    conn = sqlite3.connect(USER_DATABASE)
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
class LoginApp:
    def __init__(self, _root, geometry=None):

        # Font
        self.big_font = ("Helvetica Bold", 22)
        self.enter_font = ("Helvetica", 16)
        self.small_font = ("Helvetica Bold", 10)

        # Window Geometry
        self.frame = 400, 785
        self.login_frame = 290, 271

        # Configure main window and canvas
        self.root = _root
        self.root.title("Route Finder Login")
        if geometry is None:
            self.root.geometry(f"{self.frame[0]}x{self.frame[1]}+0+0")
        else:
            self.root.geometry(geometry)

        # Frame overlay
        self.frame_image = Image.open(f"ui_components/frame.png")
        self.frame_image = self.frame_image.resize(self.frame, Image.Resampling.LANCZOS)
        self.frame_photo = ImageTk.PhotoImage(self.frame_image)

        # Login overlay
        self.login_image = Image.open(f"ui_components/Screen 7/Foreground.png")
        self.login_image = self.login_image.resize(self.login_frame, Image.Resampling.LANCZOS)
        self.login_photo = ImageTk.PhotoImage(self.login_image)

        # UI Elements used across screens
        self.username_entry = None
        self.password_entry = None

        # Login page
        self.current_user_id = None
        self.current_user_name = None
        self.username_entry = None
        self.setup_login_page()

    # noinspection PyTypeChecker
    def setup_login_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, image=self.frame_photo).place(x=0, y=0, anchor="nw")
        login_label = tk.Label(self.root, image=self.login_photo)
        login_label.place(x=200, y=200, anchor="n")
        login_label.bind("<Button-1>", lambda e: self.login())

        tk.Label(
            self.root,
            text="Username",
            font=self.small_font,
            background="#ffffff",
            foreground="#848a85"
        ).place(x=88, y=280, anchor="w")
        self.username_entry = tk.Entry(
            self.root,
            width=23,
            font=self.enter_font,
            background="#e9e9e8",
            foreground="#848a85",
            border=None,
            borderwidth=0,
            highlightthickness=0,
        )
        self.username_entry.place(x=195, y=304, anchor="center")
        self.username_entry.focus()

        tk.Label(
            self.root,
            text="Password",
            font=self.small_font,
            background="#ffffff",
            foreground="#848a85",
        ).place(x=88, y=330, anchor="w")
        self.password_entry = tk.Entry(
            self.root,
            show="*",
            width=23,
            font=self.enter_font,
            background="#e9e9e8",
            foreground="#848a85",
            border=None,
            borderwidth=0,
            highlightthickness=0,
        )
        self.password_entry.place(x=200, y=356, anchor="center")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        conn = sqlite3.connect(USER_DATABASE)
        cursor = conn.cursor()

        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result:
            user_id, hashed_password = result
            if verify_password(password, hashed_password):
                self.current_user_id = user_id
                self.current_user_name = username
                self.launch_route_finder()
            else:
                self.display_error("* Incorrect username or password.")
        else:
            self.display_error("* Incorrect username or password.")

    def launch_route_finder(self):
        # Load user maps
        conn = sqlite3.connect(USER_DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT map_file FROM user_maps WHERE user_id = ?", (self.current_user_id,))
        maps = cursor.fetchall()
        conn.close()
        if len(maps) > 0:
            recents = self.get_recents()
            geometry = self.root.geometry()
            self.root.destroy()
            self.root = None
            from RouteFinder import RouteFinder
            route_finder_root = tk.Tk()
            RouteFinder(
                root=route_finder_root,
                rfo_filename=maps[0][0],
                recents=recents,
                callback=self.save_recents,
                username=self.current_user_name,
                geometry=geometry,
            )
            route_finder_root.mainloop()
        else:
            self.display_error("* No maps associated with this account.")

    def get_recents(self):
        conn = sqlite3.connect(USER_DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT history FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (self.current_user_id,))
            result = cursor.fetchone()
            if result:
                history_data = json.loads(result[0])
            else:
                history_data = None
        finally:
            conn.close()
        return history_data

    def save_recents(self, history_data):
        if history_data is None:
            history_data = []
        conn = sqlite3.connect(USER_DATABASE)
        cursor = conn.cursor()
        try:
            serialized_history = json.dumps(history_data)
            # Add user history to the database
            cursor.execute(
                "INSERT INTO user_history (user_id, history) VALUES (?, ?)",
                (self.current_user_id, serialized_history),
            )
            conn.commit()
        except sqlite3.Error as e:
            print("Database error:", str(e))
        finally:
            conn.close()

    def logout(self):
        self.current_user_id = None
        self.setup_login_page()

    def display_error(self, message):
        error_label = tk.Label(self.root, text=message, fg="#ff0000", font=("Helvetica", 12), bg='white')
        error_label.place(x=90, y=388, anchor=tk.W)


# Main Execution
if __name__ == "__main__":
    init_db()

    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
