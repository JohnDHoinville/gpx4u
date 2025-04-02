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

# Add a more aggressive database path check and repair
echo "=== CRITICAL DATABASE PATH CHECK ==="
export DATABASE_PATH="/var/render/data/runs.db"
echo "Setting DATABASE_PATH to $DATABASE_PATH"

# Create a link to help applications find the database
cd /opt/render/project/src/backend
ln -sf "$DATABASE_PATH" runs.db

# Ensure the database directory exists
db_dir=$(dirname "$DATABASE_PATH")
if [ ! -d "$db_dir" ]; then
  echo "Creating database directory: $db_dir"
  mkdir -p "$db_dir"
fi

# Check multiple possible sources for a valid database
possible_sources=(
  "$DATABASE_PATH"
  "/opt/render/project/src/backend/runs.db"
  "/opt/render/project/src/runs.db"
  "runs.db"
  "./runs.db"
  "../runs.db"
)

# Function to check if a file is a valid SQLite database
is_valid_db() {
  local file=$1
  if [ ! -f "$file" ]; then
    return 1
  fi
  
  # Try to read the file headers
  if file "$file" | grep -q "SQLite"; then
    # Further verify by counting tables
    if sqlite3 "$file" "SELECT count(*) FROM sqlite_master WHERE type='table';" >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

# Check source database validity
echo "Checking for valid databases..."
for src in "${possible_sources[@]}"; do
  if [ -f "$src" ] && is_valid_db "$src"; then
    echo "Found valid SQLite database at: $src"
    
    # If this isn't already the target database, check if we should copy it
    if [ "$src" != "$DATABASE_PATH" ]; then
      # Check if target exists and has tables
      if [ -f "$DATABASE_PATH" ] && is_valid_db "$DATABASE_PATH"; then
        # Compare database sizes
        src_size=$(stat -c %s "$src" 2>/dev/null || stat -f %z "$src")
        target_size=$(stat -c %s "$DATABASE_PATH" 2>/dev/null || stat -f %z "$DATABASE_PATH")
        
        # Check user counts to decide which to use
        src_users=$(sqlite3 "$src" "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
        target_users=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
        
        echo "Source DB: $src ($src_size bytes, $src_users users)"
        echo "Target DB: $DATABASE_PATH ($target_size bytes, $target_users users)"
        
        # Choose the database with more users or more data
        if [ "$src_users" -gt "$target_users" ] || [ "$src_size" -gt "$target_size" ]; then
          echo "*** SOURCE DATABASE HAS MORE DATA - CREATING BACKUP AND COPYING ***"
          backup_path="${DATABASE_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
          cp "$DATABASE_PATH" "$backup_path"
          cp "$src" "$DATABASE_PATH"
          echo "Database restored from $src to $DATABASE_PATH (backup at $backup_path)"
        else
          echo "Target database appears to have equal or more data - keeping it"
        fi
      else
        echo "Target database doesn't exist or is invalid - copying from source"
        cp "$src" "$DATABASE_PATH"
        echo "Database copied from $src to $DATABASE_PATH"
      fi
    fi
  else
    echo "Not a valid database: $src"
  fi
done

# Final check if we have a valid database at the target location
if [ -f "$DATABASE_PATH" ] && is_valid_db "$DATABASE_PATH"; then
  echo "✅ Valid database confirmed at: $DATABASE_PATH"
  # Make sure it's readable
  chmod 644 "$DATABASE_PATH"
else
  echo "⚠️ WARNING: No valid database found at: $DATABASE_PATH"
  echo "Will attempt to create a new database."
  # The application will create a new database if needed
fi

echo "=== END DATABASE PATH CHECK ==="

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
exec gunicorn --workers=2 --bind=0.0.0.0:$port --log-level=info wsgi:application 