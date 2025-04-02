#!/bin/bash
# prestart.sh - Run before application starts to ensure database persistence
# This script will:
# 1. Check multiple backup locations for database files
# 2. Evaluate the best database to use
# 3. Restore the database if needed
# 4. Create persistent backups that survive deployments

set -e  # Exit on error

echo "=== GPX4U Pre-Start Database Recovery Script ==="
echo "Running in directory: $(pwd)"
echo "Date: $(date)"

# Database Information
TARGET_DB="${DATABASE_PATH:-/opt/render/data/runs.db}"
echo "Target database path: $TARGET_DB"
TARGET_DIR="$(dirname "$TARGET_DB")"

# Backup Locations - checked in order of preference
BACKUP_LOCATIONS=(
  # GitHub persistent location where we'll store a backup
  "/opt/render/project/src/.github/db_backup"
  # Current directory 
  "/opt/render/project/src"
  # Backend directory
  "/opt/render/project/src/backend"
)

# GitHub backup location - we'll create this directory if it doesn't exist
GITHUB_BACKUP_DIR="/opt/render/project/src/.github/db_backup"
mkdir -p "$GITHUB_BACKUP_DIR"

# Function to check if a database is valid
function is_valid_db() {
  local db_file="$1"
  
  if [ ! -f "$db_file" ]; then
    return 1  # Not a file
  fi
  
  # Check if it's an SQLite database
  if ! file "$db_file" | grep -q "SQLite"; then
    return 1  # Not a SQLite file
  fi
  
  # Try to open it and check for required tables
  local tables=$(sqlite3 "$db_file" "SELECT name FROM sqlite_master WHERE type='table' AND (name='users' OR name='profile' OR name='runs')" 2>/dev/null)
  local table_count=$(echo "$tables" | wc -l)
  
  if [ "$table_count" -lt 3 ]; then
    return 1  # Missing some required tables
  fi
  
  # Check for user count (at least one user)
  local user_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM users" 2>/dev/null || echo "0")
  if [ "$user_count" -eq 0 ]; then
    return 1  # No users
  fi
  
  # Database is valid
  return 0
}

# Function to get database quality score
function get_db_quality() {
  local db_file="$1"
  
  if [ ! -f "$db_file" ]; then
    echo "0"
    return
  fi
  
  # Get run count (10 points per run)
  local run_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM runs" 2>/dev/null || echo "0")
  
  # Get user count (1 point per user)
  local user_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM users" 2>/dev/null || echo "0")
  
  # Calculate score: run_count * 10 + user_count
  local score=$((run_count * 10 + user_count))
  echo "$score"
}

# Function to evaluate and print database info
function evaluate_db() {
  local db_file="$1"
  local description="$2"
  
  if [ ! -f "$db_file" ]; then
    echo "❌ $description: Not found"
    return 1
  fi
  
  local size=$(du -h "$db_file" | cut -f1)
  
  if is_valid_db "$db_file"; then
    local run_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM runs" 2>/dev/null || echo "0")
    local user_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM users" 2>/dev/null || echo "0")
    local quality=$(get_db_quality "$db_file")
    echo "✅ $description: Valid database (${size}, ${user_count} users, ${run_count} runs, score: ${quality})"
    return 0
  else
    echo "❌ $description: Invalid database (${size})"
    return 1
  fi
}

# Check if the target database exists and is valid
echo "Checking target database..."
if evaluate_db "$TARGET_DB" "Target Database"; then
  TARGET_QUALITY=$(get_db_quality "$TARGET_DB")
  echo "Target database is valid with quality score ${TARGET_QUALITY}"
  
  # Create a backup of the valid database in the GitHub backup location
  echo "Creating backup of valid database..."
  cp "$TARGET_DB" "${GITHUB_BACKUP_DIR}/runs.db.backup"
  echo "✅ Backup created at ${GITHUB_BACKUP_DIR}/runs.db.backup"
else
  TARGET_QUALITY=0
  echo "Target database is invalid or missing. Will need to restore."
fi

# Look for the best backup database
echo "Searching for valid backup databases..."
BEST_BACKUP=""
BEST_QUALITY=0

for LOCATION in "${BACKUP_LOCATIONS[@]}"; do
  for DB_FILE in "${LOCATION}/runs.db" "${LOCATION}/runs.db.backup" "${LOCATION}/uploaded_runs.db"; do
    if [ -f "$DB_FILE" ] && is_valid_db "$DB_FILE"; then
      DB_QUALITY=$(get_db_quality "$DB_FILE")
      
      echo "Found valid database at ${DB_FILE} with quality ${DB_QUALITY}"
      
      # Update best backup if this one is better
      if [ "$DB_QUALITY" -gt "$BEST_QUALITY" ]; then
        BEST_BACKUP="$DB_FILE"
        BEST_QUALITY="$DB_QUALITY"
      fi
    fi
  done
done

# If we found a backup and it's better than the target, restore it
if [ -n "$BEST_BACKUP" ] && [ "$BEST_QUALITY" -gt "$TARGET_QUALITY" ]; then
  echo "Found better database backup at ${BEST_BACKUP} (quality: ${BEST_QUALITY} vs target: ${TARGET_QUALITY})"
  
  # Create target directory if it doesn't exist
  mkdir -p "$TARGET_DIR"
  
  # Create a backup of the current database if it exists
  if [ -f "$TARGET_DB" ]; then
    BACKUP_NAME="${TARGET_DB}.before_restore.$(date +%Y%m%d_%H%M%S)"
    cp "$TARGET_DB" "$BACKUP_NAME"
    echo "Created backup of current database at ${BACKUP_NAME}"
  fi
  
  # Copy the backup to the target location
  cp "$BEST_BACKUP" "$TARGET_DB"
  echo "✅ Restored database from ${BEST_BACKUP} to ${TARGET_DB}"
  
  # Create a backup in the GitHub directory so it's preserved across deployments
  cp "$BEST_BACKUP" "${GITHUB_BACKUP_DIR}/runs.db.backup"
  echo "✅ Created persistent backup at ${GITHUB_BACKUP_DIR}/runs.db.backup"
else
  if [ "$TARGET_QUALITY" -gt 0 ]; then
    echo "Target database is the best available, no need to restore"
  elif [ -n "$BEST_BACKUP" ]; then
    echo "No valid database found in backup locations. Will use default."
  fi
fi

# Final check on target database
echo "Final database status:"
evaluate_db "$TARGET_DB" "Target Database"

# Create a symlink to the database in the backend directory for easier access
if [ -f "$TARGET_DB" ]; then
  BACKEND_LINK="/opt/render/project/src/backend/runs.db"
  ln -sf "$TARGET_DB" "$BACKEND_LINK"
  echo "Created symlink: $BACKEND_LINK -> $TARGET_DB"
fi

echo "=== Pre-Start Database Recovery Script Complete ===" 