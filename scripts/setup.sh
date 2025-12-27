#!/bin/bash

set -e

echo "🚀 Setting up Startup Data Stack"
echo "=================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo "❌ Docker permission denied. Run: sudo usermod -aG docker $USER && newgrp docker"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.9+."
    exit 1
fi

echo "✓ All prerequisites met"
echo ""

# Check docker compose (V2 without hyphen)
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose V2 not found. Please update Docker."
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Are you in the project directory?"
    exit 1
fi

echo "Step 1: Starting PostgreSQL container..."
docker compose down  # Clean up any existing containers
docker compose up -d postgres-source

echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Wait for Postgres to be ready (max 30 seconds)
for i in {1..30}; do
    if docker exec taskflow-production-db pg_isready -U taskflow &> /dev/null; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to start"
        echo "Check logs: docker logs taskflow-production-db"
        exit 1
    fi
    sleep 1
done

echo ""
echo "Step 2: Installing Python dependencies..."
pip install -q psycopg2-binary faker pandas

echo ""
echo "Step 3: Generating sample data..."
python3 seed-data/generate_sample_data.py

echo ""
echo "Step 4: Starting remaining services..."
docker compose up -d

echo "Waiting for services to start..."
sleep 10

echo ""
echo "Step 5: Installing dbt..."
pip install -q dbt-duckdb

echo ""
echo "Step 6: Running dbt transformations..."
cd dbt
dbt deps
dbt run
cd ..

echo ""
echo "=================================="
echo "✅ Setup complete!"
echo "=================================="
echo ""

# Show summary
echo "Summary:"
USER_COUNT=$(docker exec taskflow-production-db psql -U taskflow -d taskflow_production -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs)
echo "  • Users: $USER_COUNT"
echo "  • PostgreSQL: http://localhost:5432"
echo "  • Metabase: http://localhost:3000"
echo "  • Airbyte: http://localhost:8000"
echo ""
echo "Next steps:"
echo "  1. Open Metabase at http://localhost:3000"
echo "  2. Create an account"
echo "  3. Add database: DuckDB at $(pwd)/data/taskflow.duckdb"
echo ""
