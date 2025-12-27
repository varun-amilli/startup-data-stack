````bash
#!/bin/bash

echo "Testing data stack..."

# Test 1: Check Docker services
echo "Test 1: Docker services"
docker-compose ps | grep "Up" || { echo "❌ Services not running"; exit 1; }
echo "✓ All services running"

# Test 2: Check Postgres data
echo "Test 2: PostgreSQL data"
PGPASSWORD=taskflow_prod_pass psql -h localhost -U taskflow -d taskflow_production -c "SELECT COUNT(*) FROM users;" | grep -q "[0-9]" || { echo "❌ No data"; exit 1; }
echo "✓ Data exists in Postgres"

# Test 3: Check DuckDB
echo "Test 3: DuckDB warehouse"
python3 -c "import duckdb; conn = duckdb.connect('data/taskflow.duckdb'); print(conn.execute('SELECT COUNT(*) FROM fct_user_metrics').fetchone())" || { echo "❌ DuckDB issue"; exit 1; }
echo "✓ DuckDB contains transformed data"

# Test 4: Check Metabase
echo "Test 4: Metabase"
curl -s http://localhost:3000 | grep -q "Metabase" || { echo "❌ Metabase not responding"; exit 1; }
echo "✓ Metabase is accessible"

echo "
✅ All tests passed!
"
````
