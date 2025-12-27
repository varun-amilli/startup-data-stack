# 💼 Production-Ready Data Stack for SaaS Startups

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)
[![dbt](https://img.shields.io/badge/dbt-1.11-FF694B?logo=dbt)](https://www.getdbt.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)

A complete, production-grade analytics infrastructure demonstrating modern data engineering practices. Built to showcase real-world SaaS data pipeline architecture with separation of application data and payment processing.

**Live Cost:** $0 (locally-hosted development) | **Production Cost:** ~$30-75/month (Airbyte, DigitalOcean droplet)

---

## 🎯 Project Overview

This project demonstrates a **realistic SaaS data architecture** where:
- **Application database** (TaskFlow) manages user identity and product usage
- **Payment processor** (Stripe) handles all billing and subscriptions
- **Data warehouse** combines both sources for complete analytics
- **Business intelligence** provides actionable insights through dashboards

**What makes this realistic:**
- ✅ Mirrors production SaaS architecture (Stripe for payments, separate from app DB)
- ✅ Shows real-world data integration patterns
- ✅ Implements dimensional modeling best practices
- ✅ Includes automated data pipelines and transformations

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        USER ACTIONS                             │
└────────────┬────────────────────────────┬───────────────────────┘
             │                            │
             ▼                            ▼
  ┌──────────────────────┐    ┌──────────────────────┐
  │   TaskFlow App DB    │    │   Mock Stripe API    │
  │    (PostgreSQL)      │    │      (Flask)         │
  │                      │    │                      │
  │ Manages:             │    │ Manages:             │
  │ • User accounts      │    │ • Subscriptions      │
  │ • Authentication     │    │ • Payments           │
  │ • Product events     │    │ • Invoices           │
  │ • Feature usage      │    │ • Customer records   │
  └──────────┬───────────┘    └──────────┬───────────┘
             │                           │
             │                           │ Automated Sync
             │                           │ (Python Script)
             │                           │ Every 6 hours
             ▼                           ▼
  ┌─────────────────────────────────────────────────┐
  │         PostgreSQL Data Warehouse               │
  │                                                 │
  │  ┌──────────────┐        ┌──────────────┐       │
  │  │public schema │        │stripe schema │       │
  │  │              │        │              │       │
  │  │ • users      │        │ • customers  │       │
  │  │ • events     │        │ • subs       │       │
  │  └──────────────┘        │ • charges    │       │
  │                          │ • invoices   │       │
  │                          └──────────────┘       │
  └──────────────────┬──────────────────────────────┘
                     │
                     │ dbt transformations
                     │ (nightly via cron)
                     ▼
  ┌─────────────────────────────────────────────────┐
  │        analytics schema (dbt models)            │
  │                                                 │
  │  Staging Layer (6 models):                      │
  │  • stg_users, stg_events                        │
  │  • stg_stripe_customers, stg_stripe_subs        │
  │                                                 │
  │  Marts Layer (4 models):                        │
  │  • fct_user_metrics (user behavior + revenue)   │
  │  • fct_mrr_by_month (revenue trends)            │
  │  • fct_activation_funnel (conversion)           │
  │  • fct_revenue_attribution (user journey)       │
  └──────────────────┬──────────────────────────────┘
                     │
                     │ SQL queries
                     ▼
  ┌─────────────────────────────────────────────────┐
  │              Metabase Dashboards                │
  │                                                 │
  │ • Executive Summary                             │
  └─────────────────────────────────────────────────┘
```

---

## 📊 Features & Capabilities

### Data Sources
- **500 realistic users** with signup dates spanning 6 months
- **355 activated users** (71% activation rate)
- **9,396 product events** tracking feature usage
- **200 Stripe customers** synced from mock API
- **80 active subscriptions** across 3 pricing tiers
- **679 payment transactions** with 95%+ success rate

### Analytics Models
- **10 dbt models** (6 staging, 4 marts)
- **Dimensional modeling** with proper staging → marts layers
- **Incremental materializations** for performance
- **Data quality tests** built into dbt
- **Documentation** auto-generated with dbt docs

### Business Metrics
- **Monthly Recurring Revenue (MRR)** - $12K+ from Stripe
- **Activation Rate** - 71% of signups activate
- **Conversion to Paid** - 40% of activated users subscribe
- **Engagement Scoring** - High/Medium/Low based on usage
- **Payment Success Rate** - 95%+ transaction success
- **Revenue Attribution** - Which features drive conversions
- **Cohort Analysis** - Retention by signup month
- **ARPU by Plan** - Average revenue per user

---

## 🛠️ Technologies Used

### Data Infrastructure
| Technology | Version | Purpose |
|------------|---------|---------|
| **PostgreSQL** | 15 | Application database & data warehouse |
| **dbt Core** | 1.11 | SQL-based transformations |
| **Docker Compose** | V2 | Container orchestration |
| **Python** | 3.10+ | Data generation & sync scripts |
| **Flask** | 3.0 | Mock Stripe REST API |

### Data Stack Components
| Layer | Technology | Why This Choice |
|-------|------------|-----------------|
| **Storage** | PostgreSQL with schemas | Cost-effective, supports <100GB easily |
| **Ingestion** | Python scripts (simulating Airbyte) | Demonstrates API integration skills |
| **Transformation** | dbt Core | Industry standard, version controlled |
| **Visualization** | Metabase (self-hosted) | Free, powerful, easy to use |
| **Orchestration** | Cron jobs | Simple scheduling for small scale |

### Python Dependencies
```
psycopg2-binary==2.9.9    # PostgreSQL adapter
faker==39.0.0             # Realistic test data generation
pandas==2.3.3             # Data manipulation
requests==2.31.0          # HTTP client for API calls
flask==3.0.0              # Mock API server
flask-cors==4.0.0         # CORS support for API
```

---

## 🚀 Quick Start Guide

### Prerequisites
```bash
# Required software
- Docker Desktop or Docker Engine + Docker Compose V2
- Python 3.9 or higher
- 4GB RAM minimum
- 5GB disk space

# Verify installations
docker --version          # Should be 20.10+
docker compose version    # Should show V2
python3 --version         # Should be 3.9+
```

### Installation Steps

**1. Clone the Repository**
```bash
git clone https://github.com/yourusername/startup-data-stack.git
cd startup-data-stack
```

**2. Start Docker Services**
```bash
# Start PostgreSQL, Metabase, and Mock Stripe API
docker compose up -d

# Wait for PostgreSQL to initialize
sleep 20

# Verify services are running
docker compose ps
# Should show: taskflow-production-db, mock-stripe-api, 
#              taskflow-metabase, metabase-db
```

**3. Generate Sample Data**
```bash
# Install Python dependencies
pip install -r seed-data/requirements.txt

# Generate TaskFlow application data (users + events)
python3 seed-data/generate_sample_data.py

# Expected output:
# ✓ Generated 500 users
# ✓ Generated 9,396 events
```

**4. Sync Stripe Data**
```bash
# Install sync script dependencies
pip install requests psycopg2-binary

# Sync payment data from Mock Stripe API
python3 airbyte-scripts/sync_mock_stripe.py

# Expected output:
# ✓ Synced 200 customers
# ✓ Synced 80 subscriptions
# ✓ Synced 679 charges
# ✓ Synced 679 invoices
```

**5. Run dbt Transformations**
```bash
# Install dbt
pip install dbt-postgres

# Run dbt models
cd dbt
dbt deps  # Install dependencies
dbt run   # Execute transformations

# Expected output:
# Completed successfully
# Done. PASS=10 WARN=0 ERROR=0

cd ..
```

**6. Access Metabase**
```bash
# Metabase takes 2-3 minutes to fully start
# Open in browser: http://localhost:3000
```

### Initial Metabase Setup

1. **Create Account**
   - Open http://localhost:3000
   - Email: any@example.com (local only, doesn't matter)
   - Password: choose any password
   - Company: Your Name

2. **Connect to Database**
   - Skip initial setup → Settings → Admin → Databases → Add Database
   - **Database type:** PostgreSQL
   - **Display name:** TaskFlow Analytics
   - **Host:** taskflow-production-db
   - **Port:** 5432
   - **Database name:** taskflow_production
   - **Username:** taskflow
   - **Password:** taskflow_prod_pass
   - Click "Save"

3. **Sync Schemas**
   - After saving, click "Sync database schema now"
   - Wait for sync to complete
   - You should see: `public`, `stripe`, and `analytics` schemas

4. **Explore Data**
   - Click "Browse Data" → TaskFlow Analytics
   - Explore tables in `analytics` schema
   - Start building dashboards!

---

## 📖 Usage Guide

### Daily Operations

**Check Service Status**
```bash
docker compose ps

# All services should show "Up"
# - taskflow-production-db
# - mock-stripe-api
# - taskflow-metabase
# - metabase-db
```

**View Logs**
```bash
# Metabase logs
docker logs taskflow-metabase --tail 100

# Mock Stripe API logs
docker logs mock-stripe-api --tail 50

# PostgreSQL logs
docker logs taskflow-production-db --tail 50
```

**Query Data Directly**
```bash
# Connect to PostgreSQL
docker exec -it taskflow-production-db psql -U taskflow -d taskflow_production

# Example queries:
\dt public.*          # List TaskFlow tables
\dt stripe.*          # List Stripe tables
\dt analytics.*       # List analytics models

SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM stripe.subscriptions;
SELECT COUNT(*) FROM analytics.fct_user_metrics;

\q                    # Exit
```

**Run dbt Manually**
```bash
cd dbt

# Run all models
dbt run

# Run specific model
dbt run --select fct_user_metrics

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve  # Opens at http://localhost:8080

cd ..
```

**Trigger Stripe Sync Manually**
```bash
# Sync latest data from Mock Stripe API
python3 airbyte-scripts/sync_mock_stripe.py

# Check what was synced
docker exec taskflow-production-db psql -U taskflow -d taskflow_production -c "
SELECT 
    'Customers' as table_name, COUNT(*) as records FROM stripe.customers
UNION ALL
SELECT 'Subscriptions', COUNT(*) FROM stripe.subscriptions
UNION ALL
SELECT 'Charges', COUNT(*) FROM stripe.charges
UNION ALL
SELECT 'Invoices', COUNT(*) FROM stripe.invoices;
"
```

### Automated Processes

**Cron Job for Stripe Sync** (runs every 6 hours)
```bash
# View current crontab
crontab -l

# Should show:
# 0 */6 * * * cd /home/youruser/startup-data-stack && python3 airbyte-scripts/sync_mock_stripe.py >> /tmp/stripe-sync.log 2>&1

# Check sync logs
tail -f /tmp/stripe-sync.log
```

**Schedule dbt Runs** (optional)
```bash
# Add to crontab
crontab -e

# Add this line for nightly dbt runs at 2 AM:
0 2 * * * cd /home/youruser/startup-data-stack/dbt && dbt run >> /tmp/dbt-run.log 2>&1
```

---

## 📈 Scalability

### Current Capacity
- **Users:** Supports up to 100K users
- **Events:** Handles millions of events
- **Data Volume:** Optimized for <100GB
- **Concurrent Queries:** 10-20 analysts
- **Refresh Frequency:** Hourly to daily

---

## Flexibility

**Easy Data Source Addition**
```bash
# Add a new source (e.g., Google Analytics, HubSpot)
# 1. Create sync script in airbyte-scripts/
# 2. Add staging models in dbt/models/staging/
# 3. Update marts to include new data
# 4. Run dbt
```

**Custom Metrics**
```sql
-- Add new metric by creating dbt model
-- dbt/models/marts/fct_your_metric.sql

WITH your_data AS (
    SELECT * FROM {{ ref('stg_source') }}
)

SELECT 
    your_dimension,
    your_calculation
FROM your_data
GROUP BY your_dimension
```

---

## 🚀 Deployment to Production

### Option 1: Digital Ocean Droplet ($24/month)

**Server Setup**
```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Clone repository
git clone https://github.com/yourusername/startup-data-stack.git
cd startup-data-stack

# Set environment variables
cp .env.example .env
nano .env  # Update passwords for production

# Start services
docker compose up -d

# Run initial data load
pip3 install -r seed-data/requirements.txt
python3 seed-data/generate_sample_data.py
python3 airbyte-scripts/sync_mock_stripe.py

# Setup dbt
pip3 install dbt-postgres
cd dbt && dbt run && cd ..
```

**Automated Backups**
```bash
# Create backup script
cat > /root/backup.sh << 'SCRIPT'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec taskflow-production-db pg_dump -U taskflow taskflow_production | gzip > /backups/backup_$DATE.sql.gz
find /backups -name "backup_*.sql.gz" -mtime +7 -delete
SCRIPT

chmod +x /root/backup.sh

# Schedule daily backups
crontab -e
# Add: 0 3 * * * /root/backup.sh
```

**Monitoring**
```bash
# Setup basic monitoring with Docker stats
docker stats --no-stream

# Monitor disk usage
df -h

# Check service health
docker compose ps
curl http://localhost:5001/health
curl http://localhost:3000
```

---

## 🐛 Troubleshooting

### Services Won't Start

**Problem:** Port already in use
```bash
# Check what's using the port
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :3000  # Metabase
sudo lsof -i :5001  # Mock API

# Stop conflicting service
sudo systemctl stop postgresql  # If system PostgreSQL is running

# Restart Docker services
docker compose down
docker compose up -d
```

**Problem:** Docker permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Restart Docker daemon
sudo systemctl restart docker
```

### Data Sync Issues

**Problem:** Stripe sync fails
```bash
# Check mock API is running
curl http://localhost:5001/health

# Check network connectivity
docker exec taskflow-production-db ping -c 3 mock-stripe-api

# Run sync with verbose output
python3 airbyte-scripts/sync_mock_stripe.py 2>&1 | tee sync-debug.log
```

**Problem:** No data in Stripe tables
```bash
# Verify sync completed
docker exec taskflow-production-db psql -U taskflow -d taskflow_production -c "
SELECT COUNT(*) FROM stripe.customers;
"

# Re-run sync if needed
python3 airbyte-scripts/sync_mock_stripe.py
```

### dbt Errors

**Problem:** dbt can't connect to database
```bash
cd dbt

# Test connection
dbt debug

# Check profiles.yml has correct credentials
cat profiles.yml

# Verify PostgreSQL is accessible
docker exec taskflow-production-db pg_isready -U taskflow
```

**Problem:** Model compilation errors
```bash
# Run with verbose output
dbt run --select your_model --debug

# Check compiled SQL
cat target/compiled/taskflow_analytics/models/marts/your_model.sql

# Test SQL directly in PostgreSQL
docker exec taskflow-production-db psql -U taskflow -d taskflow_production
```

### Metabase Issues

**Problem:** Can't connect to database (Note: Firewalls may prohibit setting up Metabase)
```bash
# Verify PostgreSQL is running
docker compose ps | grep taskflow-production-db

# Test connection from Metabase container
docker exec taskflow-metabase ping -c 3 taskflow-production-db

# Check credentials in docker-compose.yml match what you entered in Metabase
```

**Problem:** No data in analytics schema
```bash
# Run dbt to create analytics tables
cd dbt && dbt run && cd ..

# Verify tables exist
docker exec taskflow-production-db psql -U taskflow -d taskflow_production -c "\dt analytics.*"

# Re-sync schema in Metabase
# Settings → Admin → Databases → TaskFlow Analytics → Sync database schema now
```
---

## 📝 License

MIT License

You're free to:
- ✅ Use this for learning
- ✅ Modify for your needs
- ✅ Use in your portfolio
- ✅ Share with others

---

