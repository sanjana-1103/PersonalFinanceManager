import sqlite3

conn = sqlite3.connect("finance.db")
cursor = conn.cursor()

tables = [
    "income",
    "expenses",
    "budget",
    "savings",
    "reminders"
]

for table in tables:

    cursor.execute(f"PRAGMA table_info({table})")
    columns = [column[1] for column in cursor.fetchall()]

    if "user_id" not in columns:

        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN user_id INTEGER"
        )

        print(f"✔ user_id added to {table}")

    else:

        print(f"✔ {table} already has user_id")

conn.commit()
conn.close()

print("\nDatabase updated successfully.")