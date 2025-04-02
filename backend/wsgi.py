"""WSGI entry point for Render.com"""

import os
import sys
import time
import shutil
import sqlite3
from importlib import import_module
from pathlib import Path

# Add back-compatibility import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set production environment
os.environ['FLASK_ENV'] = 'production'

print("*** CRITICAL: Database preservation forced in WSGI entry point ***")
preserve_db = os.environ.get('PRESERVE_DATABASE', 'true').lower() in ('true', 'yes', '1')
prevent_new_db = os.environ.get('PREVENT_NEW_DATABASE', 'true').lower() in ('true', 'yes', '1')

print(f"PRESERVE_DATABASE={os.environ.get('PRESERVE_DATABASE')}, PREVENT_NEW_DATABASE={os.environ.get('PREVENT_NEW_DATABASE')}")

if preserve_db:
    print("PRESERVE_DATABASE flag is set to True - existing database will be preserved")

# Function to check if a file is a valid SQLite database with the expected tables
def is_valid_db(file_path, check_tables=True):
    if not os.path.exists(file_path):
        return False
    
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Check if this is a valid SQLite database
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] != "ok":
            return False
        
        if check_tables:
            # Verify it has the expected tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Required tables for our app
            required_tables = ['users', 'profile', 'runs']
            
            # Check if all required tables exist
            if not all(table in tables for table in required_tables):
                print(f"Missing required tables in {file_path}")
                return False
            
            # Check if there are users
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"Database at {file_path} has {user_count} users")
            
            # Check if there are runs
            cursor.execute("SELECT COUNT(*) FROM runs")
            run_count = cursor.fetchone()[0]
            print(f"Database at {file_path} has {run_count} runs")
            
            # Return True only if there are users (at minimum, the admin user)
            if user_count > 0:
                return True
        else:
            return True
        
    except Exception as e:
        print(f"Error validating database at {file_path}: {e}")
        return False
    
    return False

# Function to get database quality score (based on user and run counts)
def get_db_quality(file_path):
    if not os.path.exists(file_path):
        return -1
    
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Get run count
        cursor.execute("SELECT COUNT(*) FROM runs")
        run_count = cursor.fetchone()[0]
        
        # Quality score formula: run_count * 10 + user_count
        # This prioritizes databases with more runs
        return (run_count * 10) + user_count
        
    except Exception as e:
        print(f"Error calculating quality for {file_path}: {e}")
        return -1

# Enhanced function to find the best database from multiple locations
def find_best_database():
    # Define potential database locations in order of preference
    possible_locations = [
        os.environ.get('DATABASE_PATH'),
        '/opt/render/data/runs.db',  # Render persistent storage
        os.path.join(os.getcwd(), 'runs.db'),
        os.path.join(os.getcwd(), 'backend/runs.db'),
        os.path.join(os.path.dirname(os.getcwd()), 'runs.db'),
        './runs.db',
        '../runs.db',
        '/tmp/runs.db'
    ]
    
    # Filter out None values
    possible_locations = [loc for loc in possible_locations if loc]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_locations = [loc for loc in possible_locations if not (loc in seen or seen.add(loc))]
    
    print(f"Searching for valid databases in {len(unique_locations)} locations")
    
    valid_dbs = []
    for loc in unique_locations:
        if is_valid_db(loc):
            quality = get_db_quality(loc)
            size = os.path.getsize(loc) if os.path.exists(loc) else 0
            valid_dbs.append({
                'path': loc,
                'quality': quality,
                'size': size
            })
            print(f"Found valid database at {loc} with quality score {quality} and size {size} bytes")
    
    if not valid_dbs:
        print("No valid databases found in any location")
        return None
    
    # Sort by quality score (descending)
    valid_dbs.sort(key=lambda x: x['quality'], reverse=True)
    best_db = valid_dbs[0]
    
    print(f"Selected best database at {best_db['path']} with quality score {best_db['quality']}")
    return best_db['path']

# Set database path - critical section
db_path = os.environ.get('DATABASE_PATH')
if db_path:
    print(f"Using DATABASE_PATH from environment: {db_path}")
    
    # Create the database directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")
        except Exception as e:
            print(f"Warning: Could not create database directory {db_dir}: {e}")
    
    # If the database doesn't exist at the expected location, search for the best one
    if not os.path.exists(db_path):
        print(f"No existing database found at {db_path}")
        best_db_path = find_best_database()
        
        if best_db_path and best_db_path != db_path:
            print(f"Found better database at {best_db_path}, copying to {db_path}")
            try:
                # Create backup directory if it doesn't exist
                backup_dir = os.path.join(db_dir, "backups")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir, exist_ok=True)
                
                # Get timestamp for backup name
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                
                # Copy the best database to the proper location
                shutil.copy2(best_db_path, db_path)
                print(f"Successfully copied database from {best_db_path} to {db_path}")
                
                # Create a symlink to the database to help applications find it
                for link_name in ['./runs.db', 'runs.db', '../runs.db']:
                    try:
                        if os.path.exists(link_name):
                            os.remove(link_name)
                        os.symlink(db_path, link_name)
                        print(f"Created symlink {link_name} -> {db_path}")
                    except Exception as e:
                        print(f"Could not create symlink {link_name}: {e}")
            except Exception as e:
                print(f"Error copying database: {e}")
        else:
            print(f"No better database found. A new one will be created at {db_path} if needed.")
else:
    # No database path set, set a default
    db_path = '/var/render/data/runs.db'
    os.environ['DATABASE_PATH'] = db_path
    print(f"Set DATABASE_PATH to default: {db_path}")

# Try to import Flask-CORS for handling CORS
try:
    import flask_cors
    print("Successfully imported flask_cors")
except ImportError:
    print("Flask-CORS not installed. Attempting to install...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask-cors"])
        import flask_cors
        print("Successfully installed and imported flask_cors")
    except Exception as e:
        print(f"Failed to install Flask-CORS: {e}")
        print("CORS support will not be available")

# Import the application
try:
    from server import app as application
except ModuleNotFoundError:
    try:
        # Try relative import
        from .server import app as application
    except (ImportError, ModuleNotFoundError):
        try:
            import server
            application = server.app
        except:
            # Last resort fallback
from server import app
            application = app

# For Render.com Gunicorn configuration
app = application

# For local development
if __name__ == "__main__":
    # Get port from environment variable, default to 5001
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting development server on port {port}")
    app.run(host='0.0.0.0', port=port)