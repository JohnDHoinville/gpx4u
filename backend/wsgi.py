"""WSGI entry point for Render.com"""

import os
import sys
import shutil
import time

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# CRITICAL: FORCE DATABASE PRESERVATION IN PRODUCTION
os.environ['PRESERVE_DATABASE'] = 'true'
os.environ['PREVENT_NEW_DATABASE'] = 'true'
print(f"*** CRITICAL: Database preservation forced in WSGI entry point ***")
print(f"PRESERVE_DATABASE=true, PREVENT_NEW_DATABASE=true")

# Check for database preservation flag
preserve_db = os.environ.get('PRESERVE_DATABASE', 'true').lower() == 'true'
print(f"PRESERVE_DATABASE flag is set to {preserve_db} - {'existing database will be preserved' if preserve_db else 'a new database may be created if needed'}")

# Get database path from environment
db_path = os.environ.get('DATABASE_PATH')
if db_path:
    print(f"Using DATABASE_PATH from environment: {db_path}")
    
    # Check if the database already exists
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path) / 1024.0
        print(f"FOUND EXISTING DATABASE at {db_path} (size: {db_size:.2f} KB)")
        print("*** PRESERVING EXISTING DATABASE - NO MODIFICATIONS WILL BE MADE ***")
        
        # Create a backup of the existing database for safety
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"runs_{timestamp}_wsgi.db")
        try:
            shutil.copy2(db_path, backup_path)
            print(f"Created database backup at {backup_path}")
        except Exception as e:
            print(f"Warning: Could not create database backup: {e}")
    else:
        # Database doesn't exist at persistent location
        # But we will NOT copy from deployment directory here
        # This is handled in start_render.sh before this script runs
        print(f"No existing database found at {db_path}")
        print(f"A new database will be created if needed (handled by startup script)")
        
        # Ensure the database directory exists
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                print(f"Created database directory: {db_dir}")
            except Exception as e:
                print(f"Warning: Could not create directory {db_dir}: {e}")
else:
    # Default to a path in the data directory
    data_dir = os.path.join(os.environ.get('HOME', '.'), 'data')
    try:
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        db_path = os.path.join(data_dir, 'runs.db')
        os.environ['DATABASE_PATH'] = db_path
        print(f"Set DATABASE_PATH to default: {db_path}")
    except Exception as e:
        print(f"Warning: Could not set up default database path: {e}")
        # Last resort fallback
        db_path = 'runs.db'
        os.environ['DATABASE_PATH'] = db_path
        print(f"Falling back to local database: {db_path}")

# Import the Flask app - MUST be after environment setup
from server import app

# For Render.com Gunicorn configuration
# This is the object Gunicorn expects
application = app

# Only used for direct execution
if __name__ == "__main__":
    # Render expects binding to PORT env var on 0.0.0.0
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask development server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)