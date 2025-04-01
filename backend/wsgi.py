"""WSGI entry point for Render.com"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Check for database preservation flag
preserve_db = os.environ.get('PRESERVE_DATABASE', 'true').lower() == 'true'
if preserve_db:
    print("PRESERVE_DATABASE flag is set to true - existing database will be preserved")
else:
    print("PRESERVE_DATABASE flag is set to false - a new database may be created if needed")

# Get database path from environment
db_path = os.environ.get('DATABASE_PATH')
if db_path:
    print(f"Using DATABASE_PATH from environment: {db_path}")
    
    # Check if the database already exists
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path) / 1024.0
        print(f"FOUND EXISTING DATABASE at {db_path} (size: {db_size:.2f} KB)")
        print("*** PRESERVING EXISTING DATABASE - NO MODIFICATIONS WILL BE MADE ***")
    else:
        # Ensure the database directory exists
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                print(f"Created database directory: {db_dir}")
            except Exception as e:
                print(f"Warning: Could not create directory {db_dir}: {e}")
                
        print(f"No existing database found at {db_path} - a new one will be created")
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