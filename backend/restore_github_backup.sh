#!/bin/bash
# restore_github_backup.sh - Restores the database from the GitHub backup

set -e  # Exit on error

echo "=== GPX4U GitHub Backup Restoration Script ==="
echo "Running in directory: $(pwd)"
echo "Date: $(date)"

# Define paths
GITHUB_BACKUP_PATH="/opt/render/project/src/.github/db_backup/runs.db.backup"
TARGET_PATH="${DATABASE_PATH:-/var/render/data/runs.db}"

# Check if the backup exists
if [ ! -f "$GITHUB_BACKUP_PATH" ]; then
  echo "❌ ERROR: No backup found at $GITHUB_BACKUP_PATH"
  exit 1
fi

# Get info about the backup
BACKUP_SIZE=$(du -h "$GITHUB_BACKUP_PATH" | cut -f1)
echo "Found backup at $GITHUB_BACKUP_PATH (size: $BACKUP_SIZE)"

# Check if it's a valid SQLite database
if ! file "$GITHUB_BACKUP_PATH" | grep -q "SQLite"; then
  echo "❌ ERROR: Backup is not a valid SQLite database"
  exit 1
fi

# Check if it has the required tables
TABLES=$(sqlite3 "$GITHUB_BACKUP_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND (name='users' OR name='profile' OR name='runs')" 2>/dev/null)
TABLE_COUNT=$(echo "$TABLES" | wc -l)
if [ "$TABLE_COUNT" -lt 3 ]; then
  echo "❌ ERROR: Backup is missing required tables"
  exit 1
fi

# Get counts from the backup
USER_COUNT=$(sqlite3 "$GITHUB_BACKUP_PATH" "SELECT COUNT(*) FROM users" 2>/dev/null || echo "0")
RUN_COUNT=$(sqlite3 "$GITHUB_BACKUP_PATH" "SELECT COUNT(*) FROM runs" 2>/dev/null || echo "0")
echo "Backup contains $USER_COUNT users and $RUN_COUNT runs"

# Create a backup of the current database if it exists
if [ -f "$TARGET_PATH" ]; then
  BACKUP_NAME="${TARGET_PATH}.before_restore.$(date +%Y%m%d_%H%M%S)"
  cp "$TARGET_PATH" "$BACKUP_NAME"
  echo "Created backup of current database at $BACKUP_NAME"
fi

# Ensure the target directory exists
mkdir -p "$(dirname "$TARGET_PATH")"

# Copy the backup to the target location
cp "$GITHUB_BACKUP_PATH" "$TARGET_PATH"
echo "✅ Successfully restored database from GitHub backup to $TARGET_PATH"

# Set appropriate permissions
chmod 644 "$TARGET_PATH"
echo "Set permissions on database file"

echo "=== Database Restoration Complete ==="
echo "You may need to restart the application to see the changes." 