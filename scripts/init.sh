````bash
#!/bin/bash

set -e

echo "🚀 Initializing Startup Data Stack..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required but not installed."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 required but not installed."; exit 1; }

echo "✓ Prerequisites check passed"

# Create data directory
mkdir -p data
mkdir -p data/warehouse

# Copy env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
fi

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d

echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q -r seed-data/requirements.txt

# Generate sample data
echo "Generating sample data..."
python3 seed-data/generate_sample_data.py

# Install dbt
echo "Installing dbt..."
pip install -q dbt-duckdb

# Run dbt
echo "Running dbt transformations..."
cd dbt
dbt deps
dbt run
cd ..

echo "
✅ Setup complete!

Access your services:
- Metabase: http://localhost:3000
- Airbyte: http://localhost:8000

Next steps:
1. Open Metabase and create an account
2. Connect to DuckDB at: $(pwd)/data/taskflow.duckdb
3. Import dashboards from dashboards/metabase_dashboards.json

Happy analyzing! 📊
"
````
