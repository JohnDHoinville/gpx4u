#!/bin/bash
# Debug script for database issues on Render.com

set -e  # Exit on error

echo "=== Database Debug Script ==="
echo "Environment: $FLASK_ENV"
echo "Working directory: $(pwd)"

# Check environment variables
echo "DATABASE_PATH: $DATABASE_PATH"
echo "PRESERVE_DATABASE: $PRESERVE_DATABASE"
echo "PREVENT_NEW_DATABASE: $PREVENT_NEW_DATABASE"

# Check if DATABASE_PATH is set
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
  echo "ERROR: Database directory does not exist: $db_dir"
else
  echo "Database directory exists"
  echo "Directory contents:"
  ls -la "$db_dir"
fi

# Check database file
if [ -f "$DATABASE_PATH" ]; then
  db_size=$(stat -c %s "$DATABASE_PATH" 2>/dev/null || stat -f %z "$DATABASE_PATH")
  echo "Database file exists at: $DATABASE_PATH"
  echo "Database size: $(numfmt --to=iec-i --suffix=B $db_size 2>/dev/null || echo "$db_size bytes")"
  
  # Use sqlite3 to check database structure and contents
  echo "=== Database Schema ==="
  sqlite3 "$DATABASE_PATH" ".schema"
  
  echo "=== Database Stats ==="
  echo "Users:"
  sqlite3 "$DATABASE_PATH" "SELECT id, username, created_at FROM users;"
  
  echo "Run count:"
  sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM runs;"
  
  echo "User run counts:"
  sqlite3 "$DATABASE_PATH" "SELECT user_id, COUNT(*) FROM runs GROUP BY user_id;"
  
  echo "Recent runs:"
  sqlite3 "$DATABASE_PATH" "SELECT id, user_id, date, total_distance FROM runs ORDER BY created_at DESC LIMIT 5;"
else
  echo "ERROR: Database file does not exist at: $DATABASE_PATH"
  
  # Look for other possible database locations
  echo "Searching for database files:"
  find /opt/render -name "*.db" 2>/dev/null || echo "No database files found in /opt/render"
  find /opt/render/project -name "*.db" 2>/dev/null || echo "No database files found in /opt/render/project"
  
  echo "Local database files:"
  find . -name "*.db" -type f
fi

# Check deployment database
deploy_db="/opt/render/project/src/backend/runs.db"
if [ -f "$deploy_db" ]; then
  db_size=$(stat -c %s "$deploy_db" 2>/dev/null || stat -f %z "$deploy_db")
  echo "Deployment database exists at: $deploy_db"
  echo "Deployment database size: $(numfmt --to=iec-i --suffix=B $db_size 2>/dev/null || echo "$db_size bytes")"
  
  echo "=== Deployment Database Stats ==="
  echo "Users:"
  sqlite3 "$deploy_db" "SELECT id, username, created_at FROM users;"
  
  echo "Run count:"
  sqlite3 "$deploy_db" "SELECT COUNT(*) FROM runs;"
else
  echo "No deployment database found at: $deploy_db"
fi

echo "=== End of Database Debug Script ===" 