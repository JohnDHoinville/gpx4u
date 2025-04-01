#!/bin/bash
# Simple database backup script for Render.com deployments
# This script creates a backup of the production database without modifying it

# Exit on any error
set -e

echo "=== Database Backup Script ==="
DATE=$(date +"%Y-%m-%d_%H-%M-%S")

# Default paths
DB_PATH=${DATABASE_PATH:-"runs.db"}
BACKUP_DIR="/opt/render/data/backups"
BACKUP_PATH="${BACKUP_DIR}/runs_${DATE}.db"

echo "Production database: $DB_PATH"

# Check if this is a SQLite database
if [[ "$DATABASE_URL" == "" ]]; then
  # Create backup directory if it doesn't exist
  if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
  fi

  # Check if the database exists
  if [ -f "$DB_PATH" ]; then
    echo "Creating backup: $BACKUP_PATH"
    # Use a simple copy for SQLite
    cp "$DB_PATH" "$BACKUP_PATH"
    echo "Backup completed successfully"
    echo "Backup size: $(du -h "$BACKUP_PATH" | cut -f1)"
    
    # Keep only the 5 most recent backups
    echo "Cleaning up old backups..."
    ls -t $BACKUP_DIR/runs_*.db | tail -n +6 | xargs rm -f 2>/dev/null || true
    echo "Current backups:"
    ls -la $BACKUP_DIR/runs_*.db | head -n 5
  else
    echo "Warning: Database file not found at $DB_PATH, no backup created"
  fi
else
  echo "PostgreSQL database detected, skipping SQLite backup"
  # For PostgreSQL, you could add pg_dump here if needed
fi

echo "=== Backup Process Complete ===" 