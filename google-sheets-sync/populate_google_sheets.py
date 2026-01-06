# Creating sample data for a Google Sheet.
# Startups typically rely on Excel or Google Sheets for their data collection and usage.
# I'm simulating such a dataset to demonstrate how spreadsheets can be brought into a proper data infrastructure setup.

import gspread
from google.oauth2.service_account import Credentials
from faker import Faker
import random
from datetime import datetime, timedelta
import json

# Initialize Faker
fake = Faker()
Faker.seed(42)
random.seed(42)

# Setup Google Sheets connection
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = Credentials.from_service_account_file(
    'google-credentials.json',
    scopes=SCOPES
)

client = gspread.authorize(creds)

# Open the spreadsheet (replace with your sheet name)
SHEET_NAME = "TaskFlow App Data"
spreadsheet = client.open(SHEET_NAME)

print(f"✓ Connected to Google Sheet: {SHEET_NAME}")

# Generate Users Data
print("\nGenerating 500 users...")
users_data = [['user_id', 'email', 'name', 'company', 'created_at', 'activated_at']]

start_date = datetime.now() - timedelta(days=180)

for i in range(1, 501):
    signup_date = start_date + timedelta(days=random.randint(0, 180))
    
    # 70% activate within 7 days
    activated = random.random() < 0.7
    activated_at = signup_date + timedelta(hours=random.randint(1, 168)) if activated else None
    
    users_data.append([
        i,
        f'{fake.user_name()}_{i}@example.com',
        fake.name(),
        fake.company(),
        signup_date.strftime('%Y-%m-%d %H:%M:%S'),
        activated_at.strftime('%Y-%m-%d %H:%M:%S') if activated_at else ''
    ])

# Update or create Users sheet
try:
    users_sheet = spreadsheet.worksheet('Users')
    users_sheet.clear()
except:
    users_sheet = spreadsheet.add_worksheet(title='Users', rows=1000, cols=10)

users_sheet.update('A1', users_data)
print(f"✓ Uploaded {len(users_data)-1} users to 'Users' sheet")

# Generate Events Data
print("\nGenerating events for activated users...")
events_data = [['event_id', 'user_id', 'event_name', 'created_at', 'event_properties']]

event_types = [
    'project_created', 'task_created', 'task_completed',
    'team_member_invited', 'comment_added', 'file_uploaded',
    'view_dashboard', 'login'
]

event_id = 1

for user_row in users_data[1:]:  # Skip header
    user_id = user_row[0]
    activated_at_str = user_row[5]
    
    if activated_at_str:  # User is activated
        activated_at = datetime.strptime(activated_at_str, '%Y-%m-%d %H:%M:%S')
        num_events = random.randint(5, 50)
        
        event_end = min(datetime.now(), activated_at + timedelta(days=90))
        
        if event_end > activated_at:
            for _ in range(num_events):
                event_time = activated_at + timedelta(
                    seconds=random.randint(0, int((event_end - activated_at).total_seconds()))
                )
                
                event_name = random.choice(event_types)
                properties = {
                    'source': random.choice(['web', 'mobile', 'api']),
                    'duration_ms': random.randint(100, 5000)
                }
                
                events_data.append([
                    event_id,
                    user_id,
                    event_name,
                    event_time.strftime('%Y-%m-%d %H:%M:%S'),
                    json.dumps(properties)
                ])
                
                event_id += 1

# Update or create Events sheet
try:
    events_sheet = spreadsheet.worksheet('Events')
    events_sheet.clear()
except:
    events_sheet = spreadsheet.add_worksheet(title='Events', rows=10000, cols=10)

# Upload in chunks (Google Sheets has limits)
chunk_size = 5000
for i in range(0, len(events_data), chunk_size):
    chunk = events_data[i:i + chunk_size]
    if i == 0:
        events_sheet.update('A1', chunk)
    else:
        events_sheet.append_rows(chunk)
    print(f"  Uploaded events {i} to {min(i+chunk_size, len(events_data))}")

print(f"✓ Uploaded {len(events_data)-1} events to 'Events' sheet")

print("\n" + "="*60)
print("SUCCESS! Google Sheets populated with sample data")
print("="*60)
print(f"Users: {len(users_data)-1}")
print(f"Events: {len(events_data)-1}")
print(f"\nSheet URL: {spreadsheet.url}")
print("\nNext step: Run sync_from_google_sheets.py to load into PostgreSQL")
