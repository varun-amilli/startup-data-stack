import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta
import json
import time
import sys

fake = Faker()
Faker.seed(42)
random.seed(42)

# Try to connect with retries
max_retries = 5
retry_delay = 5

conn = None
for attempt in range(max_retries):
    try:
        print(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="taskflow_production",
            user="taskflow",
            password="taskflow_prod_pass",
            connect_timeout=10
        )
        print("✓ Connected successfully!")
        break
    except psycopg2.OperationalError as e:
        if attempt < max_retries - 1:
            print(f"Connection failed, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print(f"❌ Failed to connect after {max_retries} attempts")
            print(f"Error: {e}")
            sys.exit(1)

cur = conn.cursor()

# Check if tables already exist
cur.execute("""
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_name = 'users'
""")

if cur.fetchone()[0] > 0:
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    if user_count > 0:
        print(f"\n⚠️  Database already contains {user_count} users")
        response = input("Delete existing data and regenerate? (yes/no): ")
        if response.lower() != 'yes':
            print("Exiting without changes")
            sys.exit(0)
        
        print("Dropping existing tables...")
        cur.execute("DROP TABLE IF EXISTS events CASCADE")
        cur.execute("DROP TABLE IF EXISTS users CASCADE")
        conn.commit()
        print("✓ Existing data cleared")

# Create tables (ONLY users and events - Stripe handles payments)
print("Creating tables...")
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    company VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    activated_at TIMESTAMP,
    stripe_customer_id VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_name VARCHAR(255),
    event_properties JSONB,
    created_at TIMESTAMP
);
""")
conn.commit()
print("✓ Tables created")

# Generate 500 users over the past 6 months
print("Generating users...")
start_date = datetime.now() - timedelta(days=180)
users = []

for i in range(500):
    signup_date = start_date + timedelta(days=random.randint(0, 180))
    
    # 70% activate within 7 days
    activated = random.random() < 0.7
    activated_at = signup_date + timedelta(hours=random.randint(1, 168)) if activated else None
    
    user = {
        'email': f'{fake.user_name()}_{i}@example.com',
        'name': fake.name(),
        'company': fake.company(),
        'created_at': signup_date,
        'activated_at': activated_at,
        'stripe_customer_id': None  # Will be populated when they subscribe via Stripe
    }
    users.append(user)
    
    cur.execute("""
        INSERT INTO users (email, name, company, created_at, activated_at, stripe_customer_id)
        VALUES (%(email)s, %(name)s, %(company)s, %(created_at)s, %(activated_at)s, %(stripe_customer_id)s)
        RETURNING id
    """, user)
    user['id'] = cur.fetchone()[0]
    
    if (i + 1) % 100 == 0:
        print(f"  Generated {i + 1}/500 users...")

conn.commit()
print(f"✓ Generated {len(users)} users")

# Generate events for activated users
print("Generating events...")
event_types = [
    'project_created', 'task_created', 'task_completed',
    'team_member_invited', 'comment_added', 'file_uploaded',
    'view_dashboard', 'login'
]

events_count = 0
for idx, user in enumerate(users):
    if user['activated_at']:
        num_events = random.randint(5, 50)
        event_start = user['activated_at']
        event_end = min(datetime.now(), event_start + timedelta(days=90))
        
        # Skip if event_end is before event_start
        if event_end <= event_start:
            continue
            
        for _ in range(num_events):
            event_time = event_start + timedelta(
                seconds=random.randint(0, int((event_end - event_start).total_seconds()))
            )
            
            event_name = random.choice(event_types)
            properties = {
                'source': random.choice(['web', 'mobile', 'api']),
                'duration_ms': random.randint(100, 5000)
            }
            
            cur.execute("""
                INSERT INTO events (user_id, event_name, event_properties, created_at)
                VALUES (%s, %s, %s, %s)
            """, (user['id'], event_name, json.dumps(properties), event_time))
            events_count += 1
    
    if (idx + 1) % 100 == 0:
        print(f"  Processed {idx + 1}/500 users...")

conn.commit()
print(f"✓ Generated {events_count} events")

# Print summary
print("\n" + "="*60)
print("TASKFLOW DATABASE SEED SUMMARY")
print("="*60)
print("TaskFlow manages:")
cur.execute("SELECT COUNT(*) FROM users")
print(f"  Users: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM users WHERE activated_at IS NOT NULL")
print(f"  Activated users: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM events")
print(f"  Product events: {cur.fetchone()[0]}")
print("\nStripe manages (via API):")
print("  Subscriptions, Charges, Invoices")
print("  (Synced separately via mock-airbyte-scripts/sync_mock_stripe.py)")
print("="*60)

cur.close()
conn.close()

print("\n✅ TaskFlow data generation complete!")
print("\nNext steps:")
print("  1. Run: python3 mock-airbyte-scripts/sync_mock_stripe.py")
print("  2. Run: cd dbt && dbt run")
