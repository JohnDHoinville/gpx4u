#!/bin/bash
# Test script for database backup
# Run this locally to test the backup process

# Exit on any error
set -e

echo "=== Testing Database Backup Process ==="

# Set up test environment
export DATABASE_PATH="../runs.db"
export BACKUP_DIR="./test_backups"

# Create test backup directory
mkdir -p $BACKUP_DIR

echo "Using database: $DATABASE_PATH"
echo "Backup directory: $BACKUP_DIR"

# Create a test environment
TEST_ENV=$(cd .. && pwd)
echo "Test environment: $TEST_ENV"

# Run the backup script
echo "Running backup script..."
./backup_db.sh

# Check results
echo ""
echo "=== Backup Test Results ==="
if [ -d "$BACKUP_DIR" ]; then
  echo "Backup directory exists: Yes"
  echo "Backup files:"
  ls -la $BACKUP_DIR
  BACKUP_COUNT=$(ls -la $BACKUP_DIR | grep -c runs_)
  echo "Number of backups: $BACKUP_COUNT"
  
  if [ $BACKUP_COUNT -gt 0 ]; then
    echo "Backup test: SUCCESS"
  else
    echo "Backup test: FAILED (No backup files created)"
  fi
else
  echo "Backup directory does not exist."
  echo "Backup test: FAILED"
fi

echo ""
echo "=== Test Complete ==="

# Ask if we should clean up
read -p "Clean up test backups? (y/n): " CLEAN_UP
if [[ $CLEAN_UP == "y" ]]; then
  rm -rf $BACKUP_DIR
  echo "Test backups removed."
else
  echo "Test backups kept at $BACKUP_DIR"
fi 