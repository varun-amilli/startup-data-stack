# Sync data from Mock Stripe API to PostgreSQL
# Simulates Airbyte/Fivetran connector

import requests
import psycopg2
from psycopg2.extras import execute_batch
import json
import time
import sys
import os

# Configuration from environment variables
STRIPE_API_URL = os.getenv('STRIPE_API_URL', 'http://mock-stripe-api:5001')
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'taskflow-production-db'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'taskflow_production'),
    'user': os.getenv('POSTGRES_USER', 'taskflow'),
    'password': os.getenv('POSTGRES_PASSWORD', 'taskflow_prod_pass')
}

print("="*60)
print("MOCK STRIPE API → POSTGRESQL SYNC")
print("="*60)

# Test Stripe API connection
print(f"\n1. Testing connection to Mock Stripe API at {STRIPE_API_URL}...")
max_retries = 10
for attempt in range(max_retries):
    try:
        response = requests.get(f"{STRIPE_API_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Mock Stripe API is healthy")
            break
    except requests.exceptions.RequestException as e:
        if attempt < max_retries - 1:
            print(f"   ⚠ API not ready, retrying in 5 seconds...")
            time.sleep(5)
        else:
            print(f"   ✗ Failed to connect to Mock Stripe API after {max_retries} attempts")
            sys.exit(1)

# Connect to PostgreSQL
print(f"\n2. Connecting to PostgreSQL at {POSTGRES_CONFIG['host']}...")
max_retries = 10
conn = None

for attempt in range(max_retries):
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG, connect_timeout=10)
        print("   ✓ Connected to PostgreSQL")
        break
    except psycopg2.OperationalError as e:
        if attempt < max_retries - 1:
            print(f"   ⚠ Connection failed, retrying in 5 seconds...")
            time.sleep(5)
        else:
            print(f"   ✗ Failed to connect after {max_retries} attempts")
            print(f"   Config: {POSTGRES_CONFIG}")
            sys.exit(1)

cur = conn.cursor()

# Create stripe schema if not exists
print("\n3. Preparing Stripe schema...")
cur.execute("CREATE SCHEMA IF NOT EXISTS stripe")

# Create/recreate tables
print("   Dropping and recreating Stripe tables...")
cur.execute("DROP TABLE IF EXISTS stripe.invoices CASCADE")
cur.execute("DROP TABLE IF EXISTS stripe.charges CASCADE")
cur.execute("DROP TABLE IF EXISTS stripe.subscriptions CASCADE")
cur.execute("DROP TABLE IF EXISTS stripe.customers CASCADE")

cur.execute("""
CREATE TABLE stripe.customers (
    id VARCHAR PRIMARY KEY,
    email VARCHAR NOT NULL,
    name VARCHAR,
    created INTEGER,
    currency VARCHAR,
    delinquent BOOLEAN,
    metadata JSONB
);

CREATE TABLE stripe.subscriptions (
    id VARCHAR PRIMARY KEY,
    customer_id VARCHAR REFERENCES stripe.customers(id),
    status VARCHAR,
    plan_id VARCHAR,
    plan_amount INTEGER,
    plan_currency VARCHAR,
    plan_interval VARCHAR,
    current_period_start INTEGER,
    current_period_end INTEGER,
    created INTEGER,
    canceled_at INTEGER,
    metadata JSONB
);

CREATE TABLE stripe.charges (
    id VARCHAR PRIMARY KEY,
    amount INTEGER,
    currency VARCHAR,
    customer_id VARCHAR REFERENCES stripe.customers(id),
    status VARCHAR,
    paid BOOLEAN,
    created INTEGER,
    metadata JSONB
);

CREATE TABLE stripe.invoices (
    id VARCHAR PRIMARY KEY,
    customer_id VARCHAR REFERENCES stripe.customers(id),
    subscription_id VARCHAR REFERENCES stripe.subscriptions(id),
    amount_due INTEGER,
    amount_paid INTEGER,
    status VARCHAR,
    created INTEGER,
    currency VARCHAR,
    period_start INTEGER,
    period_end INTEGER
);
""")
conn.commit()
print("   ✓ Stripe tables created")

# Sync Customers
print("\n4. Syncing Stripe customers...")
response = requests.get(f"{STRIPE_API_URL}/v1/customers?limit=1000")
customers_data = response.json()['data']

customers_to_insert = []
for customer in customers_data:
    customers_to_insert.append((
        customer['id'],
        customer['email'],
        customer['name'],
        customer['created'],
        customer['currency'],
        customer['delinquent'],
        json.dumps(customer.get('metadata', {}))
    ))

execute_batch(cur, """
    INSERT INTO stripe.customers (id, email, name, created, currency, delinquent, metadata)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", customers_to_insert)
conn.commit()
print(f"   ✓ Synced {len(customers_to_insert)} customers")

# Sync Subscriptions
print("\n5. Syncing Stripe subscriptions...")
response = requests.get(f"{STRIPE_API_URL}/v1/subscriptions?limit=1000")
subscriptions_data = response.json()['data']

subscriptions_to_insert = []
for sub in subscriptions_data:
    subscriptions_to_insert.append((
        sub['id'],
        sub['customer'],
        sub['status'],
        sub['plan']['id'],
        sub['plan']['amount'],
        sub['plan']['currency'],
        sub['plan']['interval'],
        sub['current_period_start'],
        sub['current_period_end'],
        sub['created'],
        sub.get('canceled_at'),
        json.dumps(sub.get('metadata', {}))
    ))

execute_batch(cur, """
    INSERT INTO stripe.subscriptions 
    (id, customer_id, status, plan_id, plan_amount, plan_currency, plan_interval,
     current_period_start, current_period_end, created, canceled_at, metadata)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", subscriptions_to_insert)
conn.commit()
print(f"   ✓ Synced {len(subscriptions_to_insert)} subscriptions")

# Sync Charges
print("\n6. Syncing Stripe charges...")
response = requests.get(f"{STRIPE_API_URL}/v1/charges?limit=10000")
charges_data = response.json()['data']

charges_to_insert = []
for charge in charges_data:
    charges_to_insert.append((
        charge['id'],
        charge['amount'],
        charge['currency'],
        charge['customer'],
        charge['status'],
        charge['paid'],
        charge['created'],
        json.dumps(charge.get('metadata', {}))
    ))

# Insert in batches
batch_size = 1000
for i in range(0, len(charges_to_insert), batch_size):
    batch = charges_to_insert[i:i + batch_size]
    execute_batch(cur, """
        INSERT INTO stripe.charges (id, amount, currency, customer_id, status, paid, created, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, batch)
    if len(charges_to_insert) > batch_size:
        print(f"   Inserted charges {i+1} to {min(i+batch_size, len(charges_to_insert))}")

conn.commit()
print(f"   ✓ Synced {len(charges_to_insert)} charges")

# Sync Invoices
print("\n7. Syncing Stripe invoices...")
response = requests.get(f"{STRIPE_API_URL}/v1/invoices?limit=10000")
invoices_data = response.json()['data']

invoices_to_insert = []
for invoice in invoices_data:
    invoices_to_insert.append((
        invoice['id'],
        invoice['customer'],
        invoice['subscription'],
        invoice['amount_due'],
        invoice['amount_paid'],
        invoice['status'],
        invoice['created'],
        invoice['currency'],
        invoice['period_start'],
        invoice['period_end']
    ))

# Insert in batches
for i in range(0, len(invoices_to_insert), batch_size):
    batch = invoices_to_insert[i:i + batch_size]
    execute_batch(cur, """
        INSERT INTO stripe.invoices 
        (id, customer_id, subscription_id, amount_due, amount_paid, status, created, currency, period_start, period_end)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, batch)
    if len(invoices_to_insert) > batch_size:
        print(f"   Inserted invoices {i+1} to {min(i+batch_size, len(invoices_to_insert))}")

conn.commit()
print(f"   ✓ Synced {len(invoices_to_insert)} invoices")

# Print summary
print("\n" + "="*60)
print("STRIPE SYNC COMPLETE!")
print("="*60)
cur.execute("SELECT COUNT(*) FROM stripe.customers")
print(f"Customers: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM stripe.subscriptions")
print(f"Subscriptions: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM stripe.charges")
print(f"Charges: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM stripe.invoices")
print(f"Invoices: {cur.fetchone()[0]}")
print("="*60)

cur.close()
conn.close()

print("\n✅ Stripe sync successful!")
