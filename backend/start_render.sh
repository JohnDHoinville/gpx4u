#!/bin/bash
# Startup script for GPX4U on Render.com
# This script creates a backup of the database but NEVER modifies the production database

set -e  # Exit on error

echo "=== Starting GPX4U on Render ==="
echo "Environment: $FLASK_ENV"
echo "Working directory: $(pwd)"

# FORCE PRESERVE DATABASE TO TRUE - CRITICAL!
export PRESERVE_DATABASE="true"
echo "*** CRITICAL: PRESERVE_DATABASE forced to 'true' to prevent data loss ***"

# Ensure we're in production mode
export FLASK_ENV="production"

# Set persistent data path if not already set
if [ -z "$DATABASE_PATH" ]; then
  export DATABASE_PATH="/opt/render/data/runs.db"
  echo "Using default DATABASE_PATH: $DATABASE_PATH"
else
  echo "Using configured DATABASE_PATH: $DATABASE_PATH"
fi

# Create an additional environment variable to prevent database init
export PREVENT_NEW_DATABASE="true"
echo "PREVENT_NEW_DATABASE set to 'true' - will not initialize a new database"

# Verify that the database directory exists
db_dir=$(dirname "$DATABASE_PATH")
if [ ! -d "$db_dir" ]; then
  echo "Creating database directory: $db_dir"
  mkdir -p "$db_dir"
  echo "Database directory created: $db_dir"
fi

# IMPORTANT: If a database already exists at deployment location but not at DATABASE_PATH, copy it
deploy_db="/opt/render/project/src/backend/runs.db"
if [ ! -f "$DATABASE_PATH" ] && [ -f "$deploy_db" ]; then
  echo "FOUND DATABASE AT DEPLOYMENT LOCATION: $deploy_db"
  echo "COPYING TO PERSISTENT STORAGE: $DATABASE_PATH"
  cp "$deploy_db" "$DATABASE_PATH"
  echo "Database copied successfully"
fi

# Add extreme fallback checks for other common locations
if [ ! -f "$DATABASE_PATH" ]; then
  for potential_db in /opt/render/project/src/runs.db ./runs.db ../runs.db; do
    if [ -f "$potential_db" ]; then
      echo "FOUND DATABASE AT: $potential_db"
      echo "COPYING TO PERSISTENT STORAGE: $DATABASE_PATH"
      cp "$potential_db" "$DATABASE_PATH"
      echo "Database copied successfully"
      break
    fi
  done
fi

# Check if the database exists
if [ -f "$DATABASE_PATH" ]; then
  echo "FOUND EXISTING DATABASE at: $DATABASE_PATH"
  echo "Database size: $(du -h "$DATABASE_PATH" | cut -f1)"
  echo "*** PRESERVING EXISTING DATABASE - NO MODIFICATIONS WILL BE MADE ***"
else
  echo "WARNING: NO DATABASE FOUND at $DATABASE_PATH"
  echo "This should never happen! Looking for databases in other locations..."
  
  # Last-ditch search for any database file
  find /opt/render -name "runs.db" -type f | while read db_file; do
    echo "FOUND DATABASE AT: $db_file"
    echo "COPYING TO PERSISTENT STORAGE: $DATABASE_PATH"
    cp "$db_file" "$DATABASE_PATH"
    echo "Database copied successfully"
    break
  done
  
  # If still no database, create a minimal one
  if [ ! -f "$DATABASE_PATH" ]; then
    echo "NO DATABASE FOUND ANYWHERE - Creating a minimal database"
    echo "This is a last resort and should not normally happen"
  fi
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