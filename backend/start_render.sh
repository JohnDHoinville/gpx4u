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

# IMPORTANT: Copy deployment database ONLY if persistent database doesn't exist yet
# AND we're on the first deployment after this change
if [ ! -f "$DATABASE_PATH" ]; then
  echo "No database exists at persistent location yet: $DATABASE_PATH"
  
  deploy_db="/opt/render/project/src/backend/runs.db"
  if [ -f "$deploy_db" ]; then
    echo "FOUND DATABASE AT DEPLOYMENT LOCATION: $deploy_db"
    
    # Check if this appears to be a template database (under 100KB)
    db_size=$(stat -c %s "$deploy_db" 2>/dev/null || stat -f %z "$deploy_db")
    if [ "$db_size" -lt 102400 ]; then
      echo "WARNING: Deployment database appears to be a small template (${db_size} bytes)"
      echo "This might be an empty or template database from Git, not a production database"
      
      # Still copy it as a starting point if we have no other option
      echo "COPYING TO PERSISTENT STORAGE (as initial template): $DATABASE_PATH"
      cp "$deploy_db" "$DATABASE_PATH"
      echo "Template database copied as a starting point"
    else
      echo "COPYING TO PERSISTENT STORAGE: $DATABASE_PATH"
      cp "$deploy_db" "$DATABASE_PATH"
      echo "Database copied successfully"
    fi
  else
    echo "No database found at deployment location either"
    # Check for other database locations as a last resort
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
else
  echo "FOUND EXISTING DATABASE at: $DATABASE_PATH"
  db_size=$(stat -c %s "$DATABASE_PATH" 2>/dev/null || stat -f %z "$DATABASE_PATH")
  echo "Database size: $(numfmt --to=iec-i --suffix=B $db_size 2>/dev/null || echo "$db_size bytes")"
  echo "*** PRESERVING EXISTING DATABASE - NO MODIFICATIONS WILL BE MADE ***"
  echo "*** IMPORTANT: DATABASE FROM DEPLOYMENT LOCATION WILL BE IGNORED ***"
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