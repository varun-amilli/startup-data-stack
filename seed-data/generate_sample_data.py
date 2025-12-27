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
retry_delay = 3

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
            connect_timeout=5  # 5 second timeout
        )
        print("✓ Connected successfully!")
        break
    except psycopg2.OperationalError as e:
        if attempt < max_retries - 1:
            print(f"Connection failed: {e}")
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print(f"❌ Failed to connect after {max_retries} attempts")
            print(f"Error: {e}")
            print("\nTroubleshooting steps:")
            print("1. Check if container is running: docker compose ps")
            print("2. Check if PostgreSQL is ready: docker exec taskflow-production-db pg_isready -U taskflow")
            print("3. Check logs: docker logs taskflow-production-db")
            sys.exit(1)

if conn is None:
    print("❌ Could not establish database connection")
    sys.exit(1)

cur = conn.cursor()

# Check if tables already exist and have data
print("Checking existing data...")
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
            cur.close()
            conn.close()
            sys.exit(0)
        
        print("Dropping existing tables...")
        cur.execute("DROP TABLE IF EXISTS events CASCADE")
        cur.execute("DROP TABLE IF EXISTS stripe_charges CASCADE")
        cur.execute("DROP TABLE IF EXISTS subscriptions CASCADE")
        cur.execute("DROP TABLE IF EXISTS users CASCADE")
        conn.commit()
        print("✓ Existing data cleared")

# Create tables
print("Creating tables...")
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    company VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    activated_at TIMESTAMP,
    plan VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    stripe_subscription_id VARCHAR(255),
    plan VARCHAR(50),
    status VARCHAR(50),
    mrr_cents INTEGER,
    started_at TIMESTAMP,
    canceled_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_name VARCHAR(255),
    event_properties JSONB,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stripe_charges (
    id VARCHAR(255) PRIMARY KEY,
    customer_id VARCHAR(255),
    amount_cents INTEGER,
    status VARCHAR(50),
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
    
    # 40% of activated users subscribe
    plan = None
    if activated and random.random() < 0.4:
        plan = random.choice(['starter', 'starter', 'starter', 'professional', 'enterprise'])
    
    user = {
    	'email': f'{fake.user_name()}_{i}@example.com',
        'name': fake.name(),
        'company': fake.company(),
        'created_at': signup_date,
        'activated_at': activated_at,
        'plan': plan
    }
    users.append(user)
    
    cur.execute("""
        INSERT INTO users (email, name, company, created_at, activated_at, plan)
        VALUES (%(email)s, %(name)s, %(company)s, %(created_at)s, %(activated_at)s, %(plan)s)
        RETURNING id
    """, user)
    user['id'] = cur.fetchone()[0]
    
    if (i + 1) % 100 == 0:
        print(f"  Generated {i + 1}/500 users...")

conn.commit()
print(f"✓ Generated {len(users)} users")

# Generate subscriptions
print("Generating subscriptions...")
plan_prices = {
    'starter': 2900,
    'professional': 9900,
    'enterprise': 29900
}

subscriptions_count = 0
for user in users:
    if user['plan']:
        is_active = random.random() < 0.9
        started_at = user['activated_at'] + timedelta(days=random.randint(0, 7))
        canceled_at = None
        
        if not is_active:
            canceled_at = started_at + timedelta(days=random.randint(30, 150))
        
        cur.execute("""
            INSERT INTO subscriptions 
            (user_id, stripe_subscription_id, plan, status, mrr_cents, started_at, canceled_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user['id'],
            f"sub_{fake.uuid4()[:24]}",
            user['plan'],
            'active' if is_active else 'canceled',
            plan_prices[user['plan']],
            started_at,
            canceled_at,
            started_at
        ))
        subscriptions_count += 1

conn.commit()
print(f"✓ Generated {subscriptions_count} subscriptions")

# Generate events
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

# Generate charges
print("Generating charges...")
charges_count = 0
cur.execute("SELECT user_id, started_at, canceled_at, mrr_cents FROM subscriptions")
for user_id, started_at, canceled_at, mrr_cents in cur.fetchall():
    current_date = started_at
    end_date = canceled_at if canceled_at else datetime.now()
    
    while current_date < end_date:
        cur.execute("""
            INSERT INTO stripe_charges (id, customer_id, amount_cents, status, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            f"ch_{fake.uuid4()[:24]}",
            f"cus_{fake.uuid4()[:24]}",
            mrr_cents,
            'succeeded',
            current_date
        ))
        charges_count += 1
        current_date += timedelta(days=30)

conn.commit()
print(f"✓ Generated {charges_count} charges")

# Print summary
print("\n" + "="*60)
print("DATABASE SEED SUMMARY")
print("="*60)
cur.execute("SELECT COUNT(*) FROM users")
print(f"Total users: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM users WHERE activated_at IS NOT NULL")
print(f"Activated users: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
print(f"Active subscriptions: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM events")
print(f"Total events: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM stripe_charges")
print(f"Total charges: {cur.fetchone()[0]}")
print("="*60)

cur.execute("""
    SELECT 
        COUNT(DISTINCT CASE WHEN activated_at IS NOT NULL THEN id END)::FLOAT / COUNT(*)::FLOAT * 100 as activation_rate,
        COUNT(DISTINCT CASE WHEN plan IS NOT NULL THEN id END)::FLOAT / 
        COUNT(DISTINCT CASE WHEN activated_at IS NOT NULL THEN id END)::FLOAT * 100 as conversion_rate
    FROM users
""")
activation_rate, conversion_rate = cur.fetchone()
print(f"\nMetrics Preview:")
print(f"Activation rate: {activation_rate:.1f}%")
print(f"Activation → Paid conversion: {conversion_rate:.1f}%")

cur.execute("SELECT SUM(mrr_cents)/100.0 FROM subscriptions WHERE status = 'active'")
total_mrr = cur.fetchone()[0]
print(f"Current MRR: ${total_mrr:,.2f}")

cur.close()
conn.close()

print("\n✅ Sample data generation complete!")
