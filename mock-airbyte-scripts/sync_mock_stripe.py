# airbyte-scripts/sync_mock_stripe.py
import requests
import psycopg2
from psycopg2.extras import execute_values
import json
from datetime import datetime

# Mock Stripe API
MOCK_API_URL = "http://localhost:5001"

# PostgreSQL connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="taskflow_production",
    user="taskflow",
    password="taskflow_prod_pass"
)

def create_tables():
    """Create tables for Stripe data"""
    cur = conn.cursor()
    
    cur.execute("""
    CREATE SCHEMA IF NOT EXISTS stripe;
    
    CREATE TABLE IF NOT EXISTS stripe.customers (
        id VARCHAR(255) PRIMARY KEY,
        email VARCHAR(255),
        name VARCHAR(255),
        created BIGINT,
        currency VARCHAR(10),
        company VARCHAR(255),
        industry VARCHAR(255),
        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS stripe.subscriptions (
        id VARCHAR(255) PRIMARY KEY,
        customer_id VARCHAR(255),
        status VARCHAR(50),
        plan_id VARCHAR(50),
        plan_amount INTEGER,
        plan_currency VARCHAR(10),
        plan_interval VARCHAR(20),
        created BIGINT,
        canceled_at BIGINT,
        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS stripe.charges (
        id VARCHAR(255) PRIMARY KEY,
        customer_id VARCHAR(255),
        amount INTEGER,
        currency VARCHAR(10),
        status VARCHAR(50),
        paid BOOLEAN,
        created BIGINT,
        subscription_id VARCHAR(255),
        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS stripe.invoices (
        id VARCHAR(255) PRIMARY KEY,
        customer_id VARCHAR(255),
        subscription_id VARCHAR(255),
        amount_due INTEGER,
        amount_paid INTEGER,
        status VARCHAR(50),
        created BIGINT,
        period_start BIGINT,
        period_end BIGINT,
        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    cur.close()
    print("✓ Tables created in stripe schema")

def sync_customers():
    """Sync customers from mock API"""
    response = requests.get(f"{MOCK_API_URL}/v1/customers?limit=1000")
    customers = response.json()['data']
    
    cur = conn.cursor()
    
    values = [
        (
            c['id'],
            c['email'],
            c['name'],
            c['created'],
            c['currency'],
            c.get('metadata', {}).get('company'),
            c.get('metadata', {}).get('industry')
        )
        for c in customers
    ]
    
    execute_values(
        cur,
        """
        INSERT INTO stripe.customers (id, email, name, created, currency, company, industry)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            email = EXCLUDED.email,
            name = EXCLUDED.name,
            synced_at = CURRENT_TIMESTAMP
        """,
        values
    )
    
    conn.commit()
    cur.close()
    print(f"✓ Synced {len(customers)} customers")

def sync_subscriptions():
    """Sync subscriptions from mock API"""
    response = requests.get(f"{MOCK_API_URL}/v1/subscriptions?limit=1000")
    subscriptions = response.json()['data']
    
    cur = conn.cursor()
    
    values = [
        (
            s['id'],
            s['customer'],
            s['status'],
            s['plan']['id'],
            s['plan']['amount'],
            s['plan']['currency'],
            s['plan']['interval'],
            s['created'],
            s.get('canceled_at')
        )
        for s in subscriptions
    ]
    
    execute_values(
        cur,
        """
        INSERT INTO stripe.subscriptions 
        (id, customer_id, status, plan_id, plan_amount, plan_currency, plan_interval, created, canceled_at)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            status = EXCLUDED.status,
            canceled_at = EXCLUDED.canceled_at,
            synced_at = CURRENT_TIMESTAMP
        """,
        values
    )
    
    conn.commit()
    cur.close()
    print(f"✓ Synced {len(subscriptions)} subscriptions")

def sync_charges():
    """Sync charges from mock API"""
    response = requests.get(f"{MOCK_API_URL}/v1/charges?limit=1000")
    charges = response.json()['data']
    
    cur = conn.cursor()
    
    values = [
        (
            c['id'],
            c['customer'],
            c['amount'],
            c['currency'],
            c['status'],
            c['paid'],
            c['created'],
            c.get('metadata', {}).get('subscription_id')
        )
        for c in charges
    ]
    
    execute_values(
        cur,
        """
        INSERT INTO stripe.charges 
        (id, customer_id, amount, currency, status, paid, created, subscription_id)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            status = EXCLUDED.status,
            synced_at = CURRENT_TIMESTAMP
        """,
        values
    )
    
    conn.commit()
    cur.close()
    print(f"✓ Synced {len(charges)} charges")

def sync_invoices():
    """Sync invoices from mock API"""
    response = requests.get(f"{MOCK_API_URL}/v1/invoices?limit=1000")
    invoices = response.json()['data']
    
    cur = conn.cursor()
    
    values = [
        (
            i['id'],
            i['customer'],
            i['subscription'],
            i['amount_due'],
            i['amount_paid'],
            i['status'],
            i['created'],
            i['period_start'],
            i['period_end']
        )
        for i in invoices
    ]
    
    execute_values(
        cur,
        """
        INSERT INTO stripe.invoices 
        (id, customer_id, subscription_id, amount_due, amount_paid, status, created, period_start, period_end)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            status = EXCLUDED.status,
            amount_paid = EXCLUDED.amount_paid,
            synced_at = CURRENT_TIMESTAMP
        """,
        values
    )
    
    conn.commit()
    cur.close()
    print(f"✓ Synced {len(invoices)} invoices")

if __name__ == '__main__':
    print("=" * 60)
    print("Mock Stripe API → PostgreSQL Sync")
    print("=" * 60)
    
    create_tables()
    sync_customers()
    sync_subscriptions()
    sync_charges()
    sync_invoices()
    
    conn.close()
    
    print("=" * 60)
    print("✅ Sync complete!")
    print("=" * 60)
