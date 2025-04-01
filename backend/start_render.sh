#!/bin/bash
# Startup script for GPX4U on Render.com
# This script creates a backup of the database but doesn't modify production data

set -e  # Exit on error

echo "=== Starting GPX4U on Render ==="
echo "Environment: $FLASK_ENV"
echo "Working directory: $(pwd)"

# Ensure we're in production mode
export FLASK_ENV="production"

# Set persistent data path if not already set
if [ -z "$DATABASE_PATH" ]; then
  export DATABASE_PATH="/opt/render/data/runs.db"
  echo "Using default DATABASE_PATH: $DATABASE_PATH"
else
  echo "Using configured DATABASE_PATH: $DATABASE_PATH"
fi

# Create an automatic backup, but don't modify the original database
if [ -f "./scripts/backup_db.sh" ]; then
  echo "Creating database backup..."
  chmod +x ./scripts/backup_db.sh
  ./scripts/backup_db.sh
else
  echo "Warning: Backup script not found at ./scripts/backup_db.sh"
fi

# Get port from environment - Render requires this exact approach
# Default port for Render is 10000
port="${PORT:-10000}"
echo "IMPORTANT: Binding to port $port on host 0.0.0.0 as required by Render"

# Start Gunicorn
echo "Starting Gunicorn with workers=2, bind=0.0.0.0:$port"
exec gunicorn --workers=2 --bind=0.0.0.0:$port wsgi:app 