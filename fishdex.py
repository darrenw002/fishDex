import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime

# --- Database Setup ---
conn = sqlite3.connect('fishdex.db')
cursor = conn.cursor()

# Create the Locations table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Locations (
    locationID INTEGER PRIMARY KEY AUTOINCREMENT,
    locationName TEXT UNIQUE NOT NULL
);
''')

# Create the CatchLog table
cursor.execute('''
CREATE TABLE IF NOT EXISTS CatchLog (
    catchID INTEGER PRIMARY KEY AUTOINCREMENT,
    speciesID INTEGER NOT NULL,
    datetimeCaught TEXT NOT NULL,
    locationID INTEGER NOT NULL,
    photo BLOB,
    FOREIGN KEY (speciesID) REFERENCES ReferenceSpecies(ID) ON DELETE CASCADE,
    FOREIGN KEY (locationID) REFERENCES Locations(locationID) ON DELETE CASCADE
);
''')

# Create the Species table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Species (
    speciesID INTEGER PRIMARY KEY,
    quantityCaught INTEGER DEFAULT 0,
    orderDiscovered INTEGER UNIQUE,
    FOREIGN KEY (speciesID) REFERENCES ReferenceSpecies(ID) ON DELETE CASCADE
);
''')

conn.commit()
conn.close()

# --- Tkinter UI ---
root = tk.Tk()
root.title("FishDex")
root.geometry("800x600")  # Set window size

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# --- Home Tab ---
home_tab = ttk.Frame(notebook)
notebook.add(home_tab, text="Home")

new_entry_button = ttk.Button(home_tab, text="New Entry")
new_entry_button.pack(pady=10)

quit_button = ttk.Button(home_tab, text="Quit", command=root.quit)
quit_button.pack(pady=10)

# --- Catch Log Tab ---
catch_log_tab = ttk.Frame(notebook)
notebook.add(catch_log_tab, text="Catch Log")

catch_log_search_frame = ttk.Frame(catch_log_tab)
catch_log_search_frame.pack(fill="x", pady=5)

catch_log_search = ttk.Entry(catch_log_search_frame, width=50)
catch_log_search.pack(side="left", padx=5)

catch_log_table = ttk.Treeview(catch_log_tab, columns=("Catch ID", "Species ID", "Date Caught", "Location"), show="headings")
catch_log_table.heading("Catch ID", text="Catch ID")
catch_log_table.heading("Species ID", text="Species ID")
catch_log_table.heading("Date Caught", text="Date Caught")
catch_log_table.heading("Location", text="Location")
catch_log_table.pack(fill="both", expand=True, pady=5)

# --- Species Tab ---
species_tab = ttk.Frame(notebook)
notebook.add(species_tab, text="Species")

species_search_frame = ttk.Frame(species_tab)
species_search_frame.pack(fill="x", pady=5)

species_search = ttk.Entry(species_search_frame, width=50)
species_search.pack(side="left", padx=5)

species_table = ttk.Treeview(species_tab, columns=("Species ID", "Quantity Caught", "Order Discovered"), show="headings")
species_table.heading("Species ID", text="Species ID")
species_table.heading("Quantity Caught", text="Quantity Caught")
species_table.heading("Order Discovered", text="Order Discovered")
species_table.pack(fill="both", expand=True, pady=5)

# --- Functions to Refresh Data ---
def refresh_catch_log():
    for row in catch_log_table.get_children():
        catch_log_table.delete(row)
    conn = sqlite3.connect('fishdex.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.catchID, c.speciesID, c.datetimeCaught, l.locationName 
        FROM CatchLog c
        JOIN Locations l ON c.locationID = l.locationID
    ''')
    rows = cursor.fetchall()
    for row in rows:
        catch_log_table.insert("", "end", values=row)
    conn.close()

def refresh_species():
    for row in species_table.get_children():
        species_table.delete(row)
    conn = sqlite3.connect('fishdex.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT speciesID, quantityCaught, orderDiscovered 
        FROM Species
    ''')
    rows = cursor.fetchall()
    for row in rows:
        species_table.insert("", "end", values=row)
    conn.close()

# --- New Entry Popup Function ---
def open_new_entry_popup():
    popup = tk.Toplevel(root)
    popup.title("New Entry")
    popup.geometry("400x450")

    # Fish ID
    tk.Label(popup, text="Fish ID:").pack(pady=5)
    fish_id_entry = ttk.Entry(popup, width=30)
    fish_id_entry.pack(pady=5)

    # Location
    tk.Label(popup, text="Location Name:").pack(pady=5)
    location_name_entry = ttk.Entry(popup, width=30)
    location_name_entry.pack(pady=5)

    # Datetime
    tk.Label(popup, text="Datetime (YYYY-MM-DD HH:MM):").pack(pady=5)
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    datetime_entry = ttk.Entry(popup, width=30)
    datetime_entry.insert(0, current_datetime)
    datetime_entry.pack(pady=5)

    # Photo Upload
    def upload_photo():
        file_path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, 'rb') as file:
                binary_data = file.read()
            photo_label.photo_data = binary_data  # Store binary data as an attribute
            photo_label.config(text="Photo Selected")

    tk.Label(popup, text="Photo:").pack(pady=5)
    photo_label = tk.Label(popup, text="No file selected", fg="gray")
    photo_label.pack(pady=5)
    photo_button = ttk.Button(popup, text="Upload Photo", command=upload_photo)
    photo_button.pack(pady=5)

    # Submit Button
    def submit_entry():
        fish_id = fish_id_entry.get()
        location_name = location_name_entry.get()
        datetime_value = datetime_entry.get()
        photo_data = getattr(photo_label, 'photo_data', None)  # Retrieve binary data

        # Input validation
        if not fish_id or not location_name or not datetime_value:
            messagebox.showerror("Error", "All fields except photo are required.")
            return

        # Validate datetime format
        try:
            datetime_obj = datetime.datetime.strptime(datetime_value, "%Y-%m-%d %H:%M")
            if datetime_obj > datetime.datetime.now():
                messagebox.showerror("Error", "Datetime cannot be in the future.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid datetime format. Use YYYY-MM-DD HH:MM.")
            return

        # Insert data into database
        try:
            conn = sqlite3.connect('fishdex.db')
            cursor = conn.cursor()

            # Insert location if it doesn't exist
            cursor.execute("INSERT OR IGNORE INTO Locations (locationName) VALUES (?)", (location_name,))
            conn.commit()

            # Get location ID
            cursor.execute("SELECT locationID FROM Locations WHERE locationName = ?", (location_name,))
            location_id = cursor.fetchone()[0]

            # Insert or update Species
            cursor.execute("SELECT COUNT(*) FROM Species WHERE speciesID = ?", (fish_id,))
            species_exists = cursor.fetchone()[0] > 0

            if species_exists:
                cursor.execute("UPDATE Species SET quantityCaught = quantityCaught + 1 WHERE speciesID = ?", (fish_id,))
            else:
                cursor.execute("SELECT MAX(orderDiscovered) FROM Species")
                max_order = cursor.fetchone()[0] or 0
                new_order_discovered = max_order + 1
                cursor.execute("INSERT INTO Species (speciesID, quantityCaught, orderDiscovered) VALUES (?, 1, ?)", (fish_id, new_order_discovered))

            # Insert into CatchLog
            cursor.execute('''
                INSERT INTO CatchLog (speciesID, datetimeCaught, locationID, photo)
                VALUES (?, ?, ?, ?)
            ''', (fish_id, datetime_value, location_id, photo_data))

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "New entry added successfully!")
            popup.destroy()

            # Refresh views
            refresh_catch_log()
            refresh_species()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add entry: {e}")

    ttk.Button(popup, text="Submit", command=submit_entry).pack(pady=10)
    ttk.Button(popup, text="Cancel", command=popup.destroy).pack(pady=10)

new_entry_button.config(command=open_new_entry_popup)

# Initial load of data
refresh_catch_log()
refresh_species()

root.mainloop()
