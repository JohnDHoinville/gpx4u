#!/bin/bash
# Database restoration script for Render.com

set -e  # Exit on error

echo "=== Database Restoration Script ==="
echo "Environment: $FLASK_ENV"
echo "Working directory: $(pwd)"

# Check for uploaded database
UPLOADED_DB="./uploaded_runs.db"
if [ ! -f "$UPLOADED_DB" ]; then
  echo "ERROR: No uploaded database found at $UPLOADED_DB"
  echo "Please upload your database file as 'uploaded_runs.db' first."
  exit 1
fi

# Check environment variables
echo "DATABASE_PATH: $DATABASE_PATH"
if [ -z "$DATABASE_PATH" ]; then
  export DATABASE_PATH="/opt/render/data/runs.db"
  echo "Using default DATABASE_PATH: $DATABASE_PATH"
else
  echo "Using configured DATABASE_PATH: $DATABASE_PATH"
fi

# Check database directory
db_dir=$(dirname "$DATABASE_PATH")
echo "Database directory: $db_dir"
if [ ! -d "$db_dir" ]; then
  echo "Creating database directory: $db_dir"
  mkdir -p "$db_dir"
else
  echo "Database directory exists"
fi

# Backup existing database if it exists
if [ -f "$DATABASE_PATH" ]; then
  BACKUP_PATH="${DATABASE_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
  echo "Backing up existing database to: $BACKUP_PATH"
  cp "$DATABASE_PATH" "$BACKUP_PATH"
  echo "Backup completed successfully."
  
  # Show info about current database
  db_size=$(stat -c %s "$DATABASE_PATH" 2>/dev/null || stat -f %z "$DATABASE_PATH")
  echo "Current database size: $(numfmt --to=iec-i --suffix=B $db_size 2>/dev/null || echo "$db_size bytes")"
  
  echo "Current database users:"
  sqlite3 "$DATABASE_PATH" "SELECT id, username, created_at FROM users;" || echo "Failed to query database."
  
  echo "Current database run count:"
  sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM runs;" || echo "Failed to query database."
else
  echo "No existing database to back up."
fi

# Show info about uploaded database
uploaded_size=$(stat -c %s "$UPLOADED_DB" 2>/dev/null || stat -f %z "$UPLOADED_DB")
echo "Uploaded database size: $(numfmt --to=iec-i --suffix=B $uploaded_size 2>/dev/null || echo "$uploaded_size bytes")"

echo "Uploaded database users:"
sqlite3 "$UPLOADED_DB" "SELECT id, username, created_at FROM users;" || echo "Failed to query uploaded database."

echo "Uploaded database run count:"
sqlite3 "$UPLOADED_DB" "SELECT COUNT(*) FROM runs;" || echo "Failed to query uploaded database."

# Confirm restoration
read -p "Are you sure you want to restore this database? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Database restoration cancelled."
  exit 0
fi

# Copy the database
echo "Copying uploaded database to: $DATABASE_PATH"
cp "$UPLOADED_DB" "$DATABASE_PATH"
echo "Database restored successfully."

# Verify the restoration
echo "Verifying restored database..."
if [ -f "$DATABASE_PATH" ]; then
  restored_size=$(stat -c %s "$DATABASE_PATH" 2>/dev/null || stat -f %z "$DATABASE_PATH")
  echo "Restored database size: $(numfmt --to=iec-i --suffix=B $restored_size 2>/dev/null || echo "$restored_size bytes")"
  
  echo "Restored database users:"
  sqlite3 "$DATABASE_PATH" "SELECT id, username, created_at FROM users;" || echo "Failed to query restored database."
  
  echo "Restored database run count:"
  sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM runs;" || echo "Failed to query restored database."
  
  if [ "$restored_size" -eq "$uploaded_size" ]; then
    echo "RESTORATION SUCCESSFUL: Database sizes match."
  else
    echo "WARNING: Database sizes do not match."
  fi
else
  echo "ERROR: Database restoration failed. File not found at $DATABASE_PATH"
  exit 1
fi

echo "=== Database Restoration Complete ===" 