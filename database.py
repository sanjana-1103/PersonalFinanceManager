import sqlite3

# Connect to the database (creates it if it doesn't exist)
connection = sqlite3.connect("finance.db")

# Create a cursor object
cursor = connection.cursor()

# -----------------------------
# Users Table
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL

)
""")

# -----------------------------
# Expenses Table
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    note TEXT,
    date TEXT NOT NULL

)
""")

# -----------------------------
# Income Table
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS income (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    source TEXT NOT NULL,
    note TEXT,
    date TEXT NOT NULL

)
""")

# -----------------------------
# Budget Table
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS budget (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monthly_budget REAL NOT NULL

)
""")

# -----------------------------
# Savings Goal Table
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS savings (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_amount REAL NOT NULL

)
""")

# -----------------------------
# Bill Reminder Table
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS reminders (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_name TEXT NOT NULL,
    amount REAL NOT NULL,
    due_date TEXT NOT NULL

)
""")
# Save changes
connection.commit()

# Close connection
connection.close()

print("✅ Database created successfully!")