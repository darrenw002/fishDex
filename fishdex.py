import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import tkinter.font as tkFont
from PIL import Image, ImageTk


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
root.geometry("1000x600")  # Set window size

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)


def treeview_sort_column(treeview, col, reverse):
    """Sort Treeview column when the header is clicked."""
    # Get all items in the Treeview
    data = [(treeview.set(child, col), child) for child in treeview.get_children('')]

    # Try to sort numerically; fallback to string sorting
    try:
        data.sort(key=lambda t: float(t[0]), reverse=reverse)
    except ValueError:
        data.sort(key=lambda t: t[0].lower(), reverse=reverse)

    # Rearrange items in sorted order
    for index, (_, item) in enumerate(data):
        treeview.move(item, '', index)

    # Reverse sorting for next click
    treeview.heading(col, command=lambda: treeview_sort_column(treeview, col, not reverse))


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

# Search Bar Frame
catch_log_search_frame = ttk.Frame(catch_log_tab)
catch_log_search_frame.pack(fill="x", pady=5)

# Search Bar
catch_log_search = ttk.Entry(catch_log_search_frame, width=50)
catch_log_search.pack(side="left", padx=5)
catch_log_search.bind("<KeyRelease>", lambda e: refresh_catch_log(filter_text=catch_log_search.get()))

# Treeview for Catch Log
catch_log_table = ttk.Treeview(
    catch_log_tab,
    columns=("Catch ID", "Common Name", "Scientific Name", "Datetime Caught", "Location"),
    show="headings"
)
catch_log_table.heading("Catch ID", text="Catch Number", command=lambda: treeview_sort_column(catch_log_table, "Catch ID", False))
catch_log_table.heading("Common Name", text="Common Name", command=lambda: treeview_sort_column(catch_log_table, "Common Name", False))
catch_log_table.heading("Scientific Name", text="Scientific Name", command=lambda: treeview_sort_column(catch_log_table, "Scientific Name", False))
catch_log_table.heading("Datetime Caught", text="Date Caught", command=lambda: treeview_sort_column(catch_log_table, "Datetime Caught", False))
catch_log_table.heading("Location", text="Location Caught", command=lambda: treeview_sort_column(catch_log_table, "Location", False))
catch_log_table.pack(fill="both", expand=True, pady=5)


def on_catch_log_row_click(event):
    """Handle row click in Catch Log to display full-size image or a no-image message."""
    # Get selected item
    selected_item = catch_log_table.selection()
    if not selected_item:
        return

    # Get the Catch ID from the selected row
    catch_id = catch_log_table.item(selected_item, "values")[0]

    # Query the database for the photo blob
    conn = sqlite3.connect('fishdex.db')
    cursor = conn.cursor()
    cursor.execute("SELECT photo FROM CatchLog WHERE catchID = ?", (catch_id,))
    result = cursor.fetchone()
    conn.close()

    # Check if a photo exists and is a valid binary object
    if result and isinstance(result[0], (bytes, bytearray)):  # Ensure it's a binary object
        photo_blob = result[0]
        # Create a popup to display the image
        popup = tk.Toplevel(root)
        popup.title(f"Catch ID: {catch_id} Photo")

        # Convert blob to an image and display it
        from PIL import Image, ImageTk
        import io

        try:
            image = Image.open(io.BytesIO(photo_blob))
            # Get image dimensions and set the popup size dynamically
            img_width, img_height = image.size
            popup.geometry(f"{img_width}x{img_height}")  # Resize popup to match image dimensions
            photo_image = ImageTk.PhotoImage(image)

            label = tk.Label(popup, image=photo_image)
            label.image = photo_image  # Keep a reference to avoid garbage collection
            label.pack(fill="both", expand=True)

        except Exception as e:
            # Handle corrupted image data
            popup.destroy()
            messagebox.showerror("Error", f"Unable to display image for Catch ID: {catch_id}\n{e}")

    else:  # No valid photo available
        messagebox.showinfo("No Image", f"No image available for Catch ID: {catch_id}")




# Bind the row click event
catch_log_table.bind("<ButtonRelease-1>", on_catch_log_row_click)

# Scrollbars for Treeview
tree_scroll_y = ttk.Scrollbar(catch_log_tab, orient="vertical", command=catch_log_table.yview)
tree_scroll_y.pack(side="right", fill="y")
catch_log_table.configure(yscrollcommand=tree_scroll_y.set)


# --- Species Tab ---
species_tab = ttk.Frame(notebook)
notebook.add(species_tab, text="Species")

# Search Bar Frame for Species Tab
species_search_frame = ttk.Frame(species_tab)
species_search_frame.pack(fill="x", pady=5)

# Search Bar
species_search = ttk.Entry(species_search_frame, width=50)
species_search.pack(side="left", padx=5)

# Bind Search Bar to Species Refresh Function
species_search.bind("<KeyRelease>", lambda e: refresh_species(filter_text=species_search.get()))

# Treeview for Species Tab
species_table = ttk.Treeview(
    species_tab,
    columns=("Species ID", "Common Name", "Scientific Name", "Quantity Caught", "Order Discovered", "First Caught Date", "First Location Discovered"),
    show="headings"
)
species_table.heading("Species ID", text="Species ID", command=lambda: treeview_sort_column(species_table, "Species ID", False))
species_table.heading("Common Name", text="Common Name", command=lambda: treeview_sort_column(species_table, "Common Name", False))
species_table.heading("Scientific Name", text="Scientific Name", command=lambda: treeview_sort_column(species_table, "Scientific Name", False))
species_table.heading("Quantity Caught", text="Quantity Caught", command=lambda: treeview_sort_column(species_table, "Quantity Caught", False))
species_table.heading("Order Discovered", text="Order Discovered", command=lambda: treeview_sort_column(species_table, "Order Discovered", False))
species_table.heading("First Caught Date", text="Date Discovered", command=lambda: treeview_sort_column(species_table, "First Caught Date", False))
species_table.heading("First Location Discovered", text="Location Discovered", command=lambda: treeview_sort_column(species_table, "First Location Discovered", False))
species_table.pack(fill="both", expand=True, pady=5)


# Scrollbars for Treeview
species_scroll_y = ttk.Scrollbar(species_tab, orient="vertical", command=species_table.yview)
species_scroll_y.pack(side="right", fill="y")
species_table.configure(yscrollcommand=species_scroll_y.set)


# --- Functions to Refresh Data ---
def adjust_treeview_column_width(treeview):
    """Dynamically adjust column widths based on content."""
    font = tkFont.Font()  # Default font for Treeview
    for col in treeview["columns"]:
        max_width = font.measure(col)  # Start with the column header width
        for child in treeview.get_children():
            item_text = str(treeview.set(child, col))
            max_width = max(max_width, font.measure(item_text))
        # Add some padding
        treeview.column(col, width=max_width + 0) # Edit +0 for padding

def refresh_catch_log(filter_text=""):
    """Refresh the Catch Log Treeview and optionally filter rows."""
    # Clear the existing rows in the Treeview
    for row in catch_log_table.get_children():
        catch_log_table.delete(row)

    # Connect to the database
    conn = sqlite3.connect('fishdex.db')
    cursor = conn.cursor()

    # SQL query to fetch data with default sorting by Catch ID descending
    query = '''
        SELECT
            c.catchID,  -- Catch ID
            rs.commonName,  -- Common Name
            rs.scientificName AS scientificName,  -- Full Scientific Name
            c.datetimeCaught,  -- Datetime Caught
            COALESCE(l.locationName, 'Unknown') AS locationName  -- Location Name
        FROM CatchLog c
        LEFT JOIN Locations l ON c.locationID = l.locationID
        LEFT JOIN ReferenceSpecies rs ON c.speciesID = rs.ID
        ORDER BY c.catchID DESC;  -- Default sorting by Catch ID descending
    '''
    cursor.execute(query)
    rows = cursor.fetchall()

    # Filter rows if a search filter is provided
    if filter_text.strip():
        filter_text = filter_text.lower()
        rows = [
            row for row in rows
            if any(filter_text in str(value).lower() for value in row)
        ]

    # Insert rows into the Treeview
    for row in rows:
        catch_log_table.insert("", "end", values=row)

    # Close the database connection
    conn.close()

    # Adjust column widths dynamically
    adjust_treeview_column_width(catch_log_table)




def refresh_species(filter_text=""):
    """Refresh the Species Treeview and optionally filter rows."""
    # Clear the existing rows in the Treeview
    for row in species_table.get_children():
        species_table.delete(row)

    # Connect to the database
    conn = sqlite3.connect('fishdex.db')
    cursor = conn.cursor()

    # SQL query to fetch data with default sorting by Order Discovered descending
    cursor.execute('''
        SELECT
            s.speciesID,  -- Species ID
            rs.commonName,  -- Common Name from ReferenceSpecies
            rs.scientificName,  -- Scientific Name from ReferenceSpecies
            s.quantityCaught,  -- Quantity Caught from Species
            s.orderDiscovered,  -- Order Discovered from Species
            MIN(c.datetimeCaught) AS firstCaughtDate,  -- First Date Caught
            COALESCE(
                (SELECT l.locationName
                 FROM CatchLog c2
                 JOIN Locations l ON c2.locationID = l.locationID
                 WHERE c2.speciesID = s.speciesID
                 ORDER BY c2.datetimeCaught ASC
                 LIMIT 1),
                'Unknown'
            ) AS firstLocationDiscovered  -- First Location Discovered
        FROM Species s
        LEFT JOIN ReferenceSpecies rs ON s.speciesID = rs.ID
        LEFT JOIN CatchLog c ON s.speciesID = c.speciesID
        GROUP BY s.speciesID
        ORDER BY s.orderDiscovered DESC;  -- Default sorting by Order Discovered descending
    ''')
    rows = cursor.fetchall()

    # Filter rows if a search filter is provided
    if filter_text.strip():
        filter_text = filter_text.lower()
        rows = [
            row for row in rows
            if any(filter_text in str(value).lower() for value in row)
        ]

    # Insert rows into the Treeview
    for row in rows:
        species_table.insert("", "end", values=row)

    # Close the database connection
    conn.close()

    # Adjust column widths dynamically
    adjust_treeview_column_width(species_table)



# --- New Entry Popup Function ---
def fetch_location_suggestions(value):
    """Fetch suggestions for the location field."""
    conn = sqlite3.connect('fishdex.db')
    cursor = conn.cursor()
    cursor.execute("SELECT locationName FROM Locations WHERE locationName LIKE ? LIMIT 10", (f"%{value}%",))
    suggestions = cursor.fetchall()
    conn.close()
    return [suggestion[0] for suggestion in suggestions]


def open_new_entry_popup():
    popup = tk.Toplevel(root)
    popup.title("New Entry")
    popup.geometry("400x500")

    def fetch_suggestions(field, value):
        """Fetch suggestions for autosuggestion dropdown."""
        conn = sqlite3.connect('fishdex.db')
        cursor = conn.cursor()
        query = f"""
            SELECT ID, commonName, scientificName FROM ReferenceSpecies
            WHERE {field} LIKE ? LIMIT 10;
        """
        cursor.execute(query, (f"%{value}%",))
        suggestions = cursor.fetchall()
        conn.close()
        return suggestions

    def show_suggestions(entry_widget, field, other_entry, id_entry, dropdown):
        """Update and display dropdown under the entry field."""
        value = entry_widget.get()
        if not value.strip():
            dropdown.place_forget()  # Hide dropdown when input is empty
            return

        suggestions = fetch_suggestions(field, value)
        if not suggestions:
            dropdown.place_forget()  # Hide dropdown if no suggestions
            return

        # Populate dropdown with suggestions
        dropdown.delete(0, "end")
        for suggestion in suggestions:
            dropdown.insert("end", f"{suggestion[1]} ({suggestion[2]})")

        # Position the dropdown directly below the entry widget
        x = entry_widget.winfo_x()
        y = entry_widget.winfo_y() + entry_widget.winfo_height()
        dropdown.place(x=x, y=y, width=entry_widget.winfo_width())
        dropdown.lift()  # Bring the dropdown to the top layer

        def on_select(event):
            """Handle selection from dropdown."""
            selected_index = dropdown.curselection()
            if selected_index:
                selected = suggestions[selected_index[0]]
                # Autofill both fields and ID
                entry_widget.delete(0, "end")
                entry_widget.insert(0, selected[1] if field == "commonName" else selected[2])
                other_entry.delete(0, "end")
                other_entry.insert(0, selected[2] if field == "commonName" else selected[1])
                id_entry.config(state="normal")  # Allow programmatic update
                id_entry.delete(0, "end")
                id_entry.insert(0, selected[0])
                id_entry.config(state="readonly")  # Prevent further edits
                dropdown.place_forget()  # Hide dropdown after selection

        dropdown.bind("<<ListboxSelect>>", on_select)

    # Common Name Field
    tk.Label(popup, text="Common Name:").pack(pady=5)
    common_name_entry = ttk.Entry(popup, width=30)
    common_name_entry.pack(pady=5)
    common_name_dropdown = tk.Listbox(popup, height=5)

    common_name_entry.bind(
        "<KeyRelease>", lambda e: show_suggestions(
            common_name_entry, "commonName", species_name_entry, fish_id_entry, common_name_dropdown
        )
    )
    common_name_entry.bind("<FocusIn>", lambda e: common_name_dropdown.lift())
    common_name_entry.bind("<FocusOut>", lambda e: common_name_dropdown.place_forget())

    # Scientific Name Field
    tk.Label(popup, text="Scientific Name:").pack(pady=5)
    species_name_entry = ttk.Entry(popup, width=30)
    species_name_entry.pack(pady=5)
    species_name_dropdown = tk.Listbox(popup, height=5)

    species_name_entry.bind(
        "<KeyRelease>", lambda e: show_suggestions(
            species_name_entry, "scientificName", common_name_entry, fish_id_entry, species_name_dropdown
        )
    )
    species_name_entry.bind("<FocusIn>", lambda e: species_name_dropdown.lift())
    species_name_entry.bind("<FocusOut>", lambda e: species_name_dropdown.place_forget())

    # Fish ID Field (Read-only)
    tk.Label(popup, text="Fish ID:").pack(pady=5)
    fish_id_entry = ttk.Entry(popup, width=30, state="readonly")
    fish_id_entry.pack(pady=5)

    # Location Field
    tk.Label(popup, text="Location Name:").pack(pady=5)
    location_name_entry = ttk.Entry(popup, width=30)
    location_name_entry.pack(pady=5)
    location_dropdown = tk.Listbox(popup, height=5)

    def show_location_suggestions(event):
        """Update and display dropdown under the location entry field."""
        value = location_name_entry.get()
        if not value.strip():
            location_dropdown.place_forget()  # Hide dropdown when input is empty
            return

        suggestions = fetch_location_suggestions(value)
        if not suggestions:
            location_dropdown.place_forget()  # Hide dropdown if no suggestions
            return

        # Populate dropdown with suggestions
        location_dropdown.delete(0, "end")
        for suggestion in suggestions:
            location_dropdown.insert("end", suggestion)

        # Position the dropdown directly below the entry widget
        x = location_name_entry.winfo_x()
        y = location_name_entry.winfo_y() + location_name_entry.winfo_height()
        location_dropdown.place(x=x, y=y, width=location_name_entry.winfo_width())
        location_dropdown.lift()  # Bring the dropdown to the top layer

    def on_location_select(event):
        """Handle selection from location dropdown."""
        selected_index = location_dropdown.curselection()
        if selected_index:
            selected = location_dropdown.get(selected_index)
            location_name_entry.delete(0, "end")
            location_name_entry.insert(0, selected)
            location_dropdown.place_forget()  # Hide dropdown after selection

    location_dropdown.bind("<<ListboxSelect>>", on_location_select)

    # Bind location entry field to show suggestions
    location_name_entry.bind("<KeyRelease>", show_location_suggestions)
    location_name_entry.bind("<FocusIn>", lambda e: location_dropdown.lift())
    location_name_entry.bind("<FocusOut>", lambda e: location_dropdown.place_forget())


    # Datetime Field
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
            from PIL import Image
            import io

            # Open the image
            image = Image.open(file_path)

            # Convert RGBA to RGB if necessary
            if image.mode == "RGBA":
                image = image.convert("RGB")

            # Set maximum dimensions
            max_width = 1000
            max_height = 1000

            # Resize while preserving aspect ratio
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Convert the resized image to binary data (blob)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")  # Save as JPEG to reduce size further
            binary_data = buffer.getvalue()

            # Store the binary data
            photo_label.photo_data = binary_data
            photo_label.config(text="Photo Selected")



    tk.Label(popup, text="Photo:").pack(pady=5)
    photo_label = tk.Label(popup, text="No file selected", fg="gray")
    photo_label.pack(pady=5)
    photo_button = ttk.Button(popup, text="Upload Photo", command=upload_photo)
    photo_button.pack(pady=5)

    # Submit Button
    def submit_entry():
        fish_id = fish_id_entry.get()
        common_name = common_name_entry.get()
        scientific_name = species_name_entry.get()
        location_name = location_name_entry.get()
        datetime_value = datetime_entry.get()
        photo_data = getattr(photo_label, 'photo_data', None)  # Retrieve binary data

        # Input validation
        if not fish_id or not common_name or not scientific_name or not location_name or not datetime_value:
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


    ttk.Button(popup, text="Submit", command=submit_entry).pack(pady=10)
    ttk.Button(popup, text="Cancel", command=popup.destroy).pack(pady=10)


new_entry_button.config(command=open_new_entry_popup)

# Initial load of data
refresh_catch_log()
refresh_species()

root.mainloop()
