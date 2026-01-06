from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random
import hashlib
import psycopg2
import time
import os

app = Flask(__name__)
CORS(app)

# Seed for consistent data
random.seed(42)

# Get real user emails from TaskFlow database with retry logic
def get_taskflow_user_emails():
    """Pull activated user emails from TaskFlow to create realistic matches"""
    max_retries = 10
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'taskflow-production-db'),
                port=int(os.getenv('POSTGRES_PORT', '5432')),
                database=os.getenv('POSTGRES_DB', 'taskflow_production'),
                user=os.getenv('POSTGRES_USER', 'taskflow'),
                password=os.getenv('POSTGRES_PASSWORD', 'taskflow_prod_pass'),
                connect_timeout=5
            )
            cur = conn.cursor()
            
            # Get activated users (40% of them will become Stripe customers)
            cur.execute("""
                SELECT email, name, company 
                FROM users 
                WHERE activated_at IS NOT NULL 
                ORDER BY RANDOM() 
                LIMIT 200
            """)
            
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            if results:
                print(f"✓ Connected to TaskFlow DB and found {len(results)} users")
                return [(email, name, company) for email, name, company in results]
            else:
                print("⚠ No users found in database yet, using fallback data")
                return None
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠ Attempt {attempt + 1}/{max_retries}: Cannot connect to TaskFlow DB yet: {e}")
                print(f"  Retrying in 3 seconds...")
                time.sleep(3)
            else:
                print(f"⚠ Could not connect to TaskFlow DB after {max_retries} attempts")
                print(f"  Using fallback generated data")
                return None
    
    return None

# Generate customers using TaskFlow emails
def generate_customers():
    customers = []
    base_date = datetime(2025, 1, 1)
    
    # Try to get real TaskFlow emails
    taskflow_users = get_taskflow_user_emails()
    
    if taskflow_users:
        # Use real TaskFlow user data
        print(f"Generating {len(taskflow_users)} Stripe customers from TaskFlow users...")
        for i, (email, name, company) in enumerate(taskflow_users):
            created = base_date + timedelta(days=random.randint(0, 180))
            customers.append({
                'id': f'cus_{hashlib.md5(email.encode()).hexdigest()[:24]}',
                'object': 'customer',
                'email': email,
                'name': name or f'Customer {i}',
                'created': int(created.timestamp()),
                'currency': 'usd',
                'delinquent': False,
                'metadata': {
                    'company': company or 'Unknown',
                    'industry': random.choice(['SaaS', 'E-commerce', 'Consulting', 'Agency'])
                }
            })
    else:
        # Fallback to generated data
        print("Generating 200 Stripe customers with fallback data...")
        for i in range(200):
            created = base_date + timedelta(days=random.randint(0, 180))
            customers.append({
                'id': f'cus_{hashlib.md5(str(i).encode()).hexdigest()[:24]}',
                'object': 'customer',
                'email': f'customer{i}@example.com',
                'name': f'Customer {i}',
                'created': int(created.timestamp()),
                'currency': 'usd',
                'delinquent': False,
                'metadata': {
                    'company': f'Company {i}',
                    'industry': random.choice(['SaaS', 'E-commerce', 'Consulting', 'Agency'])
                }
            })
    
    return customers

def generate_subscriptions(customers):
    subscriptions = []
    plans = [
        {'id': 'starter', 'amount': 2900, 'name': 'Starter'},
        {'id': 'professional', 'amount': 9900, 'name': 'Professional'},
        {'id': 'enterprise', 'amount': 29900, 'name': 'Enterprise'}
    ]
    
    # 40% of customers have subscriptions
    for customer in random.sample(customers, k=int(len(customers) * 0.4)):
        plan = random.choice(plans)
        created = datetime.fromtimestamp(customer['created']) + timedelta(days=random.randint(1, 14))
        
        # 90% active, 10% canceled
        status = random.choice(['active'] * 9 + ['canceled'])
        canceled_at = None
        if status == 'canceled':
            canceled_at = int((created + timedelta(days=random.randint(30, 120))).timestamp())
        
        subscriptions.append({
            'id': f'sub_{hashlib.md5(customer["id"].encode()).hexdigest()[:24]}',
            'object': 'subscription',
            'customer': customer['id'],
            'status': status,
            'plan': {
                'id': plan['id'],
                'object': 'plan',
                'amount': plan['amount'],
                'currency': 'usd',
                'interval': 'month',
                'product': plan['name']
            },
            'current_period_start': int(created.timestamp()),
            'current_period_end': int((created + timedelta(days=30)).timestamp()),
            'created': int(created.timestamp()),
            'canceled_at': canceled_at,
            'metadata': {
                'plan_name': plan['name']
            }
        })
    return subscriptions

def generate_charges(subscriptions):
    charges = []
    
    for sub in subscriptions:
        created = datetime.fromtimestamp(sub['created'])
        end_date = datetime.fromtimestamp(sub['canceled_at']) if sub['canceled_at'] else datetime.now()
        
        # Generate monthly charges
        current = created
        charge_num = 0
        while current < end_date:
            # 95% success rate
            status = 'succeeded' if random.random() < 0.95 else 'failed'
            
            charge_id_base = sub['id'] + str(charge_num)
            charge_hash = hashlib.md5(charge_id_base.encode()).hexdigest()[:24]
            
            charges.append({
                'id': f'ch_{charge_hash}',
                'object': 'charge',
                'amount': sub['plan']['amount'],
                'currency': 'usd',
                'customer': sub['customer'],
                'status': status,
                'paid': status == 'succeeded',
                'created': int(current.timestamp()),
                'metadata': {
                    'subscription_id': sub['id'],
                    'plan': sub['plan']['id']
                }
            })
            
            current += timedelta(days=30)
            charge_num += 1
            
    return charges

def generate_invoices(subscriptions):
    invoices = []
    
    for sub in subscriptions:
        created = datetime.fromtimestamp(sub['created'])
        end_date = datetime.fromtimestamp(sub['canceled_at']) if sub['canceled_at'] else datetime.now()
        
        current = created
        invoice_num = 0
        while current < end_date:
            invoice_id_base = sub['id'] + str(invoice_num)
            invoice_hash = hashlib.md5(invoice_id_base.encode()).hexdigest()[:24]
            
            invoices.append({
                'id': f'in_{invoice_hash}',
                'object': 'invoice',
                'customer': sub['customer'],
                'subscription': sub['id'],
                'amount_due': sub['plan']['amount'],
                'amount_paid': sub['plan']['amount'],
                'status': 'paid',
                'created': int(current.timestamp()),
                'currency': 'usd',
                'period_start': int(current.timestamp()),
                'period_end': int((current + timedelta(days=30)).timestamp())
            })
            
            current += timedelta(days=30)
            invoice_num += 1
            
    return invoices

# Generate all data once at startup
print("="*60)
print("Mock Stripe API - Initializing...")
print("="*60)

CUSTOMERS = generate_customers()
SUBSCRIPTIONS = generate_subscriptions(CUSTOMERS)
CHARGES = generate_charges(SUBSCRIPTIONS)
INVOICES = generate_invoices(SUBSCRIPTIONS)

print(f"✓ Generated {len(CUSTOMERS)} customers")
print(f"✓ Generated {len(SUBSCRIPTIONS)} subscriptions")
print(f"✓ Generated {len(CHARGES)} charges")
print(f"✓ Generated {len(INVOICES)} invoices")
print("="*60)

# API Endpoints
@app.route('/v1/customers', methods=['GET'])
def list_customers():
    limit = int(request.args.get('limit', 100))
    starting_after = request.args.get('starting_after', None)
    
    start_idx = 0
    if starting_after:
        for idx, cust in enumerate(CUSTOMERS):
            if cust['id'] == starting_after:
                start_idx = idx + 1
                break
    
    data = CUSTOMERS[start_idx:start_idx + limit]
    has_more = start_idx + limit < len(CUSTOMERS)
    
    return jsonify({
        'object': 'list',
        'data': data,
        'has_more': has_more,
        'url': '/v1/customers'
    })

@app.route('/v1/subscriptions', methods=['GET'])
def list_subscriptions():
    limit = int(request.args.get('limit', 100))
    status = request.args.get('status', None)
    
    data = SUBSCRIPTIONS
    if status:
        data = [s for s in data if s['status'] == status]
    
    data = data[:limit]
    
    return jsonify({
        'object': 'list',
        'data': data,
        'has_more': False,
        'url': '/v1/subscriptions'
    })

@app.route('/v1/charges', methods=['GET'])
def list_charges():
    limit = int(request.args.get('limit', 100))
    customer = request.args.get('customer', None)
    
    data = CHARGES
    if customer:
        data = [c for c in data if c['customer'] == customer]
    
    data = sorted(data, key=lambda x: x['created'], reverse=True)
    data = data[:limit]
    
    return jsonify({
        'object': 'list',
        'data': data,
        'has_more': False,
        'url': '/v1/charges'
    })

@app.route('/v1/invoices', methods=['GET'])
def list_invoices():
    limit = int(request.args.get('limit', 100))
    customer = request.args.get('customer', None)
    
    data = INVOICES
    if customer:
        data = [i for i in data if i['customer'] == customer]
    
    data = sorted(data, key=lambda x: x['created'], reverse=True)
    data = data[:limit]
    
    return jsonify({
        'object': 'list',
        'data': data,
        'has_more': False,
        'url': '/v1/invoices'
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'endpoints': [
            '/v1/customers',
            '/v1/subscriptions',
            '/v1/charges',
            '/v1/invoices'
        ],
        'total_records': {
            'customers': len(CUSTOMERS),
            'subscriptions': len(SUBSCRIPTIONS),
            'charges': len(CHARGES),
            'invoices': len(INVOICES)
        }
    })

if __name__ == '__main__':
    print("Mock Stripe API Server - Ready")
    print(f"Running on http://0.0.0.0:5001")
    print(f"Health check: http://localhost:5001/health")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
