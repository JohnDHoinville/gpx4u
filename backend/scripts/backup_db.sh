#!/bin/bash
# Simple database backup script for Render.com deployments
# This script creates a backup of the production database without modifying it

# Exit on any error
set -e

echo "=== Database Backup Script ==="
echo "WARNING: This script will only create a backup and never modify the production database"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")

# Get database path from environment variable
DB_PATH=${DATABASE_PATH:-"/opt/render/data/runs.db"}
BACKUP_DIR="/opt/render/data/backups"
BACKUP_PATH="${BACKUP_DIR}/runs_${DATE}.db"

echo "Production database path: $DB_PATH"

# Skip if DATABASE_URL is set (PostgreSQL is being used)
if [[ -n "$DATABASE_URL" ]]; then
  echo "PostgreSQL database detected, skipping SQLite backup"
  exit 0
fi

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
  echo "Creating backup directory: $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
fi

# Check if the database exists
if [ -f "$DB_PATH" ]; then
  echo "Found existing database at: $DB_PATH"
  echo "Database size: $(du -h "$DB_PATH" | cut -f1)"
  
  # Create a backup copy of the database
  echo "Creating backup: $BACKUP_PATH"
  cp "$DB_PATH" "$BACKUP_PATH"
  echo "Backup created successfully"
  echo "Backup size: $(du -h "$BACKUP_PATH" | cut -f1)"
  
  # Keep only the 5 most recent backups
  echo "Cleaning up old backups..."
  ls -t $BACKUP_DIR/runs_*.db 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
  echo "Current backups:"
  ls -la $BACKUP_DIR/runs_*.db 2>/dev/null | head -n 5 || echo "No backups found"
else
  echo "WARNING: Database file not found at $DB_PATH"
  echo "No backup created - original database doesn't exist"
fi

echo "=== Backup Process Complete ==="
# IMPORTANT: We NEVER modify the original database 