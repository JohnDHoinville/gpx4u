#!/bin/bash
# Startup script for GPX4U on Render.com
# This script NEVER modifies the production database - it only creates backups

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

# Verify that the database directory exists
db_dir=$(dirname "$DATABASE_PATH")
if [ ! -d "$db_dir" ]; then
  echo "Creating database directory: $db_dir"
  mkdir -p "$db_dir"
  echo "Database directory created: $db_dir"
fi

# Check if the database exists
if [ -f "$DATABASE_PATH" ]; then
  echo "FOUND EXISTING DATABASE at: $DATABASE_PATH"
  echo "Database size: $(du -h "$DATABASE_PATH" | cut -f1)"
  echo "*** PRESERVING EXISTING DATABASE - NO MODIFICATIONS WILL BE MADE ***"
  
  # Set preservation flag for the application
  export PRESERVE_DATABASE="true"
else
  echo "WARNING: No database found at $DATABASE_PATH"
  echo "A new database will be created by the application."
  
  # Only in this case, let the application create a new database
  export PRESERVE_DATABASE="false"
fi

# Create a backup, but NEVER modify the original database
if [ -f "$DATABASE_PATH" ]; then
  BACKUP_DIR="/opt/render/data/backups"
  mkdir -p "$BACKUP_DIR"
  BACKUP_FILE="$BACKUP_DIR/runs_$(date +%Y%m%d_%H%M%S).db"
  echo "Creating backup at: $BACKUP_FILE"
  cp "$DATABASE_PATH" "$BACKUP_FILE"
  echo "Backup created successfully"
  
  # Keep only the last 5 backups to save space
  ls -t "$BACKUP_DIR"/*.db 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
  echo "Current backups:"
  ls -la "$BACKUP_DIR"/*.db | head -n 5 || echo "No backups found"
else
  echo "No database to back up yet"
fi

# Get port from environment - Render requires this exact approach
# Default port for Render is 10000
port="${PORT:-10000}"
echo "IMPORTANT: Binding to port $port on host 0.0.0.0 as required by Render"

# Start Gunicorn
echo "Starting Gunicorn with workers=2, bind=0.0.0.0:$port"
exec gunicorn --workers=2 --bind=0.0.0.0:$port --log-level=info wsgi:app 