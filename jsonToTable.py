import sqlite3
import json

# Load JSON data
with open("fishBase.json", "r") as file:
    fish_data = json.load(file)

# Connect to the database
conn = sqlite3.connect("fishdex.db")
cursor = conn.cursor()

# Create the ReferenceSpecies table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ReferenceSpecies (
        ID INTEGER PRIMARY KEY,
        scientificName TEXT NOT NULL,
        commonName TEXT,
        imageLink TEXT,
        fishLink TEXT
    )
""")

# Insert data into the table
for fish in fish_data:
    # Check if the ID already exists
    cursor.execute("SELECT ID FROM ReferenceSpecies WHERE ID = ?", (fish["ID"],))
    if cursor.fetchone() is None:
        # Insert only if the ID does not already exist
        cursor.execute("""
            INSERT INTO ReferenceSpecies (ID, scientificName, commonName, imageLink, fishLink)
            VALUES (?, ?, ?, ?, ?)
        """, (fish["ID"], fish["scientificName"], fish["commonName"], fish["imageLink"], fish["fishLink"]))
    else:
        print(f"Skipping duplicate ID: {fish['ID']}")

# Commit and close
conn.commit()
conn.close()

print("Data successfully imported into ReferenceSpecies table!")
