# Sync TaskFlow data from Google Sheets to PostgreSQL

import gspread
from google.oauth2.service_account import Credentials
import psycopg2
from psycopg2.extras import execute_batch
import json
from datetime import datetime
import time
import sys
import os

# Google Sheets setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEET_NAME = os.getenv('GOOGLE_SHEETS_NAME', 'TaskFlow App Data')
CREDENTIALS_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'google-credentials.json')

print("="*60)
print("GOOGLE SHEETS → POSTGRESQL SYNC")
print("="*60)

# Connect to Google Sheets
print("\n1. Connecting to Google Sheets...")
try:
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open(SHEET_NAME)
    print(f"   ✓ Connected to: {SHEET_NAME}")
except Exception as e:
    print(f"   ✗ Error connecting to Google Sheets: {e}")
    sys.exit(1)

# Connect to PostgreSQL
print("\n2. Connecting to PostgreSQL...")
max_retries = 10
conn = None

postgres_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'taskflow_production'),
    'user': os.getenv('POSTGRES_USER', 'taskflow'),
    'password': os.getenv('POSTGRES_PASSWORD', 'taskflow_prod_pass')
}

for attempt in range(max_retries):
    try:
        conn = psycopg2.connect(**postgres_config, connect_timeout=10)
        print("   ✓ Connected to PostgreSQL")
        break
    except psycopg2.OperationalError as e:
        if attempt < max_retries - 1:
            print(f"   ⚠ Connection failed, retrying in 5 seconds...")
            time.sleep(5)
        else:
            print(f"   ✗ Failed to connect after {max_retries} attempts")
            sys.exit(1)

cur = conn.cursor()

# Check if tables exist
print("\n3. Preparing database tables...")
cur.execute("""
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_name = 'users'
""")

if cur.fetchone()[0] > 0:
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    if user_count > 0:
        print(f"   ⚠ Database already contains {user_count} users")
        print("   Dropping and reloading from Google Sheets...")

# Drop and recreate tables
print("   Dropping existing tables...")
cur.execute("DROP TABLE IF EXISTS events CASCADE")
cur.execute("DROP TABLE IF EXISTS users CASCADE")

print("   Creating fresh tables...")
cur.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    company VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    activated_at TIMESTAMP,
    stripe_customer_id VARCHAR(255)
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_name VARCHAR(255),
    event_properties JSONB,
    created_at TIMESTAMP
);
""")
conn.commit()
print("   ✓ Tables created")

# Sync Users from Google Sheets
print("\n4. Syncing users from Google Sheets...")
users_sheet = spreadsheet.worksheet('Users')
users_data = users_sheet.get_all_records()

users_to_insert = []
for row in users_data:
    created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
    activated_at = None
    if row.get('activated_at'):
        activated_at = datetime.strptime(row['activated_at'], '%Y-%m-%d %H:%M:%S')
    
    users_to_insert.append((
        row['user_id'],
        row['email'],
        row['name'],
        row['company'],
        created_at,
        activated_at,
        None
    ))

execute_batch(cur, """
    INSERT INTO users (id, email, name, company, created_at, activated_at, stripe_customer_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", users_to_insert)

conn.commit()
print(f"   ✓ Synced {len(users_to_insert)} users")

# Sync Events from Google Sheets
print("\n5. Syncing events from Google Sheets...")
events_sheet = spreadsheet.worksheet('Events')
events_data = events_sheet.get_all_records()

events_to_insert = []
for row in events_data:
    created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
    properties = json.loads(row['event_properties']) if row.get('event_properties') else {}
    
    events_to_insert.append((
        row['event_id'],
        row['user_id'],
        row['event_name'],
        json.dumps(properties),
        created_at
    ))

batch_size = 1000
for i in range(0, len(events_to_insert), batch_size):
    batch = events_to_insert[i:i + batch_size]
    execute_batch(cur, """
        INSERT INTO events (id, user_id, event_name, event_properties, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, batch)
    if len(events_to_insert) > batch_size:
        print(f"   Inserted events {i+1} to {min(i+batch_size, len(events_to_insert))}")

conn.commit()
print(f"   ✓ Synced {len(events_to_insert)} events")

# Print summary
print("\n" + "="*60)
print("SYNC COMPLETE!")
print("="*60)
cur.execute("SELECT COUNT(*) FROM users")
print(f"Users in PostgreSQL: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM users WHERE activated_at IS NOT NULL")
print(f"Activated users: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM events")
print(f"Events in PostgreSQL: {cur.fetchone()[0]}")
print(f"\nData source: Google Sheets")
print(f"Sheet: {SHEET_NAME}")
print("="*60)

cur.close()
conn.close()

print("\n✅ Google Sheets sync successful!")
