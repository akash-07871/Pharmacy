import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Create distributors table
c.execute("""
CREATE TABLE IF NOT EXISTS distributors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    password TEXT,
    secret_code TEXT
)
""")

# Create pharmacies table
c.execute("""
CREATE TABLE IF NOT EXISTS pharmacies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    password TEXT,
    distributor_id INTEGER,
    FOREIGN KEY(distributor_id) REFERENCES distributors(id)
)
""")

c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('backup', '123', 'backup')")

conn.commit()
conn.close()




print("Database and users created successfully!")


