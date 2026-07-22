"""
check_hr_users.py
------------------
Quick standalone utility to look up HR login credentials stored in the
local SQLite database, without importing app.py (which would also
load the Sentence-BERT model — slow and unnecessary just to read a
table).

Usage (from the recruitment_system folder):
    python3 check_hr_users.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "recruitment.db")

if not os.path.exists(DB_PATH):
    print(f"No database found at {DB_PATH}. Have you run the app at least once?")
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT id, username, password, company FROM hr_user;")
rows = cur.fetchall()
conn.close()

if not rows:
    print("No HR accounts found yet. Sign up at /hr/signup first.")
else:
    print(f"{'ID':<4} {'Username':<20} {'Password':<20} {'Company'}")
    print("-" * 64)
    for row in rows:
        print(f"{row[0]:<4} {row[1]:<20} {row[2]:<20} {row[3]}")
