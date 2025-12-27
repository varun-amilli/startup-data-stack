#!/bin/bash

echo "Verifying data stack setup..."
echo ""

# Check Postgres
echo "📊 Checking PostgreSQL data..."
if docker exec taskflow-production-db psql -U taskflow -d taskflow_production -c "\dt" > /dev/null 2>&1; then
    USERS=$(docker exec taskflow-production-db psql -U taskflow -d taskflow_production -t -c "SELECT COUNT(*) FROM users;" | xargs)
    EVENTS=$(docker exec taskflow-production-db psql -U taskflow -d taskflow_production -t -c "SELECT COUNT(*) FROM events;" | xargs)
    SUBS=$(docker exec taskflow-production-db psql -U taskflow -d taskflow_production -t -c "SELECT COUNT(*) FROM subscriptions;" | xargs)
    
    echo "  ✓ Users: $USERS"
    echo "  ✓ Events: $EVENTS"
    echo "  ✓ Subscriptions: $SUBS"
else
    echo "  ❌ Cannot connect to PostgreSQL or no tables exist"
    exit 1
fi

echo ""

# Check DuckDB
echo "📊 Checking DuckDB warehouse..."
if [ -f "data/taskflow.duckdb" ]; then
    echo "  ✓ DuckDB file exists"
    
    # Try to query it
    if python3 -c "import duckdb; conn = duckdb.connect('data/taskflow.duckdb'); tables = conn.execute('SHOW TABLES').fetchall(); print(f'  ✓ Tables: {len(tables)}'); conn.close()" 2>/dev/null; then
        :
    else
        echo "  ⚠️  DuckDB exists but has no tables. Run: cd dbt && dbt run"
    fi
else
    echo "  ❌ DuckDB file not found. Run: cd dbt && dbt run"
fi

echo ""

# Check services
echo "🐳 Checking Docker services..."
if docker ps | grep -q "taskflow-production-db"; then
    echo "  ✓ PostgreSQL running"
else
    echo "  ❌ PostgreSQL not running"
fi

if docker ps | grep -q "taskflow-metabase"; then
    echo "  ✓ Metabase running"
else
    echo "  ❌ Metabase not running"
fi

echo ""
echo "✅ Verification complete"
