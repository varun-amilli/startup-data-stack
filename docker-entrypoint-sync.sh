#!/bin/bash
set -e

echo "=========================================="
echo "Data Sync Service Starting"
echo "=========================================="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h taskflow-production-db -U taskflow; do
  echo "  PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✓ PostgreSQL is ready"

# Wait for Mock Stripe API to be ready
echo "Waiting for Mock Stripe API..."
until curl -sf http://mock-stripe-api:5001/health > /dev/null; do
  echo "  Mock API is unavailable - sleeping"
  sleep 2
done
echo "✓ Mock Stripe API is ready"

# Check if Google credentials exist
GOOGLE_CREDS_EXIST=false
if [ -f "/app/google-credentials.json" ] && [ -s "/app/google-credentials.json" ]; then
    if grep -q "service_account" /app/google-credentials.json 2>/dev/null; then
        GOOGLE_CREDS_EXIST=true
        echo "✓ Google credentials found"
    fi
fi

if [ "$GOOGLE_CREDS_EXIST" = false ]; then
    echo "⚠️  Google credentials not found or invalid"
    echo "   Google Sheets sync will be skipped"
fi

# Function to run full sync
run_sync() {
    echo ""
    echo "=========================================="
    echo "Running Data Sync: $(date)"
    echo "=========================================="
    
    # Step 1: Sync from Google Sheets (if credentials exist)
    if [ "$GOOGLE_CREDS_EXIST" = true ]; then
        echo "1. Syncing from Google Sheets..."
        cd /app && python3 google-sheets-sync/sync_from_google_sheets.py
    else
        echo "1. Skipping Google Sheets sync (no credentials)"
        echo "   Using Mock Stripe API data only"
    fi
    
    # Step 2: Sync from Mock Stripe API (FIXED PATH)
    echo "2. Syncing from Mock Stripe API..."
    cd /app && python3 mock-airbyte-scripts/sync_mock_stripe.py
    
    # Step 3: Run dbt transformations (only if we have data)
    if [ "$GOOGLE_CREDS_EXIST" = true ]; then
        echo "3. Running dbt transformations..."
        cd /app/dbt && dbt run
    else
        echo "3. Skipping dbt (no user data available)"
        echo "   dbt requires user data from Google Sheets"
    fi
    
    echo "✓ Sync completed: $(date)"
    echo "=========================================="
}

# Handle different startup modes
case "$1" in
    "cron-mode")
        echo "Starting in CRON mode (scheduled syncs)"
        
        # Set up cron jobs
        echo "0 */6 * * * cd /app && /app/entrypoint.sh sync-only >> /var/log/sync/sync.log 2>&1" > /etc/cron.d/data-sync
        chmod 0644 /etc/cron.d/data-sync
        crontab /etc/cron.d/data-sync
        
        # Run initial sync (in foreground, send to log)
        echo "Running initial sync..."
        run_sync | tee /var/log/sync/sync.log
        
        # Start cron and tail the log
        echo ""
        echo "Initial sync complete. Cron scheduled for every 6 hours."
        echo "View logs: docker logs data-sync-service -f"
        echo ""
        cron && tail -f /var/log/sync/sync.log
        ;;
        
    "sync-only")
        run_sync
        ;;
        
    "populate-sheets")
        if [ "$GOOGLE_CREDS_EXIST" = true ]; then
            echo "Populating Google Sheets with sample data..."
            cd /app && python3 google-sheets-sync/populate_google_sheets.py
        else
            echo "❌ Cannot populate Google Sheets: credentials not found"
            exit 1
        fi
        ;;
        
    "dbt-only")
        echo "Running dbt only..."
        cd /app/dbt && dbt run
        ;;
        
    "manual")
        echo "Manual mode - container will stay running"
        tail -f /dev/null
        ;;
        
    *)
        echo "Usage: $0 {cron-mode|sync-only|populate-sheets|dbt-only|manual}"
        exit 1
        ;;
esac
