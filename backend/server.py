from flask import Flask, request, jsonify, session, send_from_directory
# Try to import CORS, but if it fails, we'll handle it
try:
    from flask_cors import CORS
    has_flask_cors = True
    print("Successfully imported flask_cors")
except ImportError:
    has_flask_cors = False
    print("WARNING: flask_cors not available, CORS support will be disabled")

from dotenv import load_dotenv
import tempfile
import os
import traceback
import sys
import json
from datetime import datetime
import re
from functools import wraps
import secrets
from json import JSONEncoder
from routes.auth import auth_bp
from routes.runs import runs_bp
from routes.profile import profile_bp
from routes.admin import admin_bp
from config import config
import sqlite3
from sqlalchemy import select, func

# Use the custom encoder for all JSON responses
class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

# Add debugging and error handling
def handle_exception(e):
    """Print exception details to stderr for Render logs"""
    print('=' * 80, file=sys.stderr)
    print("Exception occurred:", file=sys.stderr)
    print(str(e), file=sys.stderr)
    print('-' * 80, file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    print('=' * 80, file=sys.stderr)
    return str(e)

# Load environment variables
load_dotenv()

# Environment
env = os.environ.get('FLASK_ENV', 'development')
print(f"Starting Flask server in {env} mode...")

# Import configuration - correct import path
try:
    from config import config
    CONFIG = config[env]
    print(f"Loaded config for environment: {env}")
except Exception as e:
    print("Error importing config:", handle_exception(e))
    
    # Create fallback config
    class FallbackConfig:
        def __init__(self):
            self.SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-dev-key')
            self.DATABASE_URI = os.environ.get('DATABASE_URL')
            self.FRONTEND_URL = os.environ.get('FRONTEND_URL', '*')
            self.DEBUG = env == 'development'
    
    CONFIG = FallbackConfig()
    print("Using fallback configuration")

# Import app modules - with better error handling
try:
    from app.running import analyze_run_file, calculate_pace_zones, analyze_elevation_impact
    print("Successfully imported running module")
except Exception as e:
    print("Error importing running module:", handle_exception(e))
    
    # Create fallback functions if needed
    def analyze_run_file(file_path):
        return {"error": "Running analysis module not available"}
    
    def calculate_pace_zones(base_pace):
        return {"error": "Pace zones calculation not available"}
    
    def analyze_elevation_impact(data):
        return {"error": "Elevation impact analysis not available"}

try:
    from app.database_adapter import RunDatabaseAdapter, safe_json_dumps
    print("Successfully imported database adapter")
except Exception as e:
    print("Error importing database adapter:", handle_exception(e))
    
    # Create fallback database adapter
    class FallbackDatabaseAdapter:
        def __init__(self):
            print("Using fallback database adapter - limited functionality")
        
        def get_user_by_username(self, username):
            return None
            
        def verify_password(self, user, password):
            return False
    
    safe_json_dumps = json.dumps
    RunDatabaseAdapter = FallbackDatabaseAdapter

# Initialize Flask app with static folder
# Use absolute path for static folder to ensure it works with any working directory
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
print(f"Using static folder: {static_folder}")

# Attempt to fix React asset paths issue by checking for asset-manifest.json
asset_manifest_path = os.path.join(static_folder, 'asset-manifest.json')
if os.path.exists(asset_manifest_path):
    print(f"Found asset-manifest.json at {asset_manifest_path}")
    try:
        with open(asset_manifest_path, 'r') as f:
            asset_manifest = json.load(f)
            print(f"Asset manifest contains {len(asset_manifest)} entries")
            for key, path in asset_manifest.items():
                if key.startswith('files.'):
                    print(f"Asset path: {key} -> {path}")
    except Exception as e:
        print(f"Error reading asset manifest: {e}")

app = Flask(__name__, static_folder=static_folder, static_url_path='')
print(f"Starting Flask server in {env} mode with static url path: ''")

# Use the custom encoder for all JSON responses
app.json_encoder = DateTimeEncoder

# Configure Flask app
app.secret_key = CONFIG.SECRET_KEY
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True only in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
    SESSION_COOKIE_NAME='running_session',  # Custom session cookie name
    SESSION_TYPE='filesystem'
)

# Configure CORS if available
try:
    if env == 'development' and has_flask_cors:
        CORS(app,
            origins=[CONFIG.FRONTEND_URL],
            methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Accept", "Cookie"],
            supports_credentials=True,
            expose_headers=["Content-Type", "Authorization", "Set-Cookie"],
            allow_credentials=True)
    elif has_flask_cors:
        # In production, the frontend is served from the same domain by Flask
        # Allow all origins since we're using the same domain
        CORS(app,
            origins=["*"],
            methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Accept", "Cookie"],
            supports_credentials=True,
            expose_headers=["Content-Type", "Authorization", "Set-Cookie"],
            allow_credentials=True)
        print("Production CORS configured to allow all origins")
    else:
        print("CORS support disabled due to missing flask_cors package")
except Exception as e:
    print("Error configuring CORS:", handle_exception(e))

# Initialize database
try:
    db = RunDatabaseAdapter()
    print("Successfully initialized database")
except Exception as e:
    print("Error initializing database:", handle_exception(e))
    # Create a minimal db instance to avoid errors later
    db = FallbackDatabaseAdapter()

# Session debugging
@app.before_request
def before_request():
    print(f"\n=== REQUEST: {request.method} {request.path} ===")
    print(f"Current session: {dict(session)}")

@app.after_request
def after_request(response):
    print(f"=== RESPONSE: {response.status_code} ===")
    print(f"Session after request: {dict(session)}")
    return response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'status': 'Backend server is running'}), 200

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    try:
        print(f"Serving path: '{path}'")
        
        # Check if path starts with /auth or /api - direct to proper route handlers
        if path.startswith('auth/') or path.startswith('api/'):
            print(f"API path detected: {path} - This should be handled by other routes")
            # Let other routes handle this
            # Flask will move on if this route doesn't return
            return jsonify({
                'error': 'Not found - path conflicts with API routes',
                'path': path
            }), 404
            
        # For the root path, serve index.html
        if not path:
            print("Serving index.html for root path")
            return send_from_directory(static_folder, 'index.html')
        
        # Handle the case where path starts with 'static/'
        if path.startswith('static/'):
            rel_path = path[7:]  # Remove 'static/' from the beginning
            full_path = os.path.join(static_folder, 'static', rel_path)
            dir_path = os.path.dirname(full_path)
            file_name = os.path.basename(full_path)
            
            if os.path.exists(full_path) and os.path.isfile(full_path):
                print(f"Serving static file from: {dir_path}, file: {file_name}")
                return send_from_directory(dir_path, file_name)
        
        # Direct file access for non-prefixed paths
        full_path = os.path.join(static_folder, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            print(f"Serving file directly: {full_path}")
            dir_path = os.path.dirname(full_path)
            file_name = os.path.basename(full_path)
            return send_from_directory(dir_path, file_name)
        
        # For all other paths, serve index.html to support SPA routing
        print(f"Path '{path}' not found as static file, serving index.html for SPA routing")
        return send_from_directory(static_folder, 'index.html')
    except Exception as e:
        error_msg = handle_exception(e)
        return jsonify({'error': f"Error serving path '{path}': {error_msg}"}), 500

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    try:
        print("\n=== Starting Analysis ===")
        if 'file' not in request.files:
            print("No file in request")
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        print(f"\nFile details:")
        print(f"Filename: {file.filename}")
        print(f"Content type: {file.content_type}")
        print(f"File size: {len(file.read())} bytes")
        file.seek(0)  # Reset file pointer after reading
        
        # Debug profile data
        print("\nSession data:", dict(session))
        print("User ID:", session.get('user_id'))
        
        pace_limit = float(request.form.get('paceLimit', 0))
        age = int(request.form.get('age', 0))
        resting_hr = int(request.form.get('restingHR', 0))
        
        # Get user profile for additional metrics
        profile = db.get_profile(session['user_id'])
        print("\nProfile data:", profile)
        
        if not file or not file.filename.endswith('.gpx'):
            print("Invalid file format")
            return jsonify({'error': 'Invalid file format'}), 400
            
        # Extract date from filename
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', file.filename)
        run_date = date_match.group(0) if date_match else datetime.now().strftime('%Y-%m-%d')
        
        # Save uploaded file temporarily
        temp_path = 'temp.gpx'
        file.save(temp_path)
        
        print("\nFile saved to:", temp_path)
        print("File exists:", os.path.exists(temp_path))
        print("File size:", os.path.getsize(temp_path))
        
        try:
            # Analyze the file
            analysis_result = analyze_run_file(
                temp_path, 
                pace_limit,
                user_age=age,
                resting_hr=resting_hr,
                weight=profile['weight'],
                gender=profile['gender']
            )
            
            if not analysis_result:
                print("Analysis returned no results")
                return jsonify({'error': 'Failed to analyze run data'}), 500
                
            # Build run_data to save in the runs table
            run_data = {
                'date': run_date,   # or datetime.now().strftime('%Y-%m-%d')
                'data': analysis_result
            }
            
            # Actually save the run
            print("\nAttempting to save run data...")
            run_id = db.save_run(session['user_id'], run_data)
            print(f"Run saved successfully with ID: {run_id}")

            return jsonify({
                'message': 'Analysis complete',
                'data': analysis_result,
                'run_id': run_id,
                'saved': True
            })
            
        except Exception as e:
            print(f"\nError during analysis:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("Full traceback:")
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"Cleaned up temporary file: {temp_path}")
                
    except Exception as e:
        print(f"\nServer error:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/compare', methods=['POST'])
@login_required
def compare_runs():
    try:
        run_ids = request.json['runIds']
        print(f"Comparing runs with IDs: {run_ids}")
        
        formatted_runs = []
        for run_id in run_ids:
            run = db.get_run_by_id(run_id)
            if run:
                try:
                    run_data = json.loads(run['data'])
                    
                    # Calculate total time for average pace
                    total_time = 0
                    for segment in run_data['fast_segments'] + run_data['slow_segments']:
                        if isinstance(segment, dict) and 'time_diff' in segment:
                            total_time += segment['time_diff']
                    
                    # Calculate average pace
                    avg_pace = total_time / run_data['total_distance'] if run_data['total_distance'] > 0 else 0
                    
                    # Calculate elevation gain
                    elevation_gain = 0
                    if 'elevation_data' in run_data:
                        elevation_changes = [point['elevation'] for point in run_data['elevation_data']]
                        elevation_gain = sum(max(0, elevation_changes[i] - elevation_changes[i-1]) 
                                          for i in range(1, len(elevation_changes)))
                    
                    formatted_run = {
                        'id': run['id'],
                        'date': run['date'],
                        'distance': run_data['total_distance'],
                        'avg_pace': avg_pace,
                        'avg_hr': run_data.get('avg_hr_all', 0),
                        'elevation_gain': elevation_gain,
                        'data': run['data'],
                        'mile_splits': run_data.get('mile_splits', [])
                    }
                    formatted_runs.append(formatted_run)
                    print(f"Formatted run for comparison: {formatted_run}")
                except Exception as e:
                    print(f"Error formatting run {run_id}: {str(e)}")
                    traceback.print_exc()
                    continue
        
        return jsonify(formatted_runs)
    except Exception as e:
        print(f"Compare error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/runs/<int:run_id>', methods=['DELETE'])
@login_required
def delete_run(run_id):
    try:
        print(f"Attempting to delete run {run_id}")
        # Verify the run belongs to the current user
        run = db.get_run_by_id(run_id, session['user_id'])
        if not run:
            print(f"Run {run_id} not found or doesn't belong to user")
            return jsonify({'error': 'Run not found'}), 404
            
        db.delete_run(run_id)
        print(f"Successfully deleted run {run_id}")
        return jsonify({'message': f'Run {run_id} deleted successfully'})
    except Exception as e:
        print(f"Error deleting run: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        profile = db.get_profile(session['user_id'])
        return jsonify(profile)
    except Exception as e:
        print(f"Error getting profile: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/profile', methods=['POST'])
@login_required
def save_profile():
    try:
        data = request.json
        age = data.get('age', 0)
        resting_hr = data.get('resting_hr', 0)
        weight = data.get('weight', 70)
        gender = data.get('gender', 1)
        
        db.save_profile(
            user_id=session['user_id'],
            age=age,
            resting_hr=resting_hr,
            weight=weight,
            gender=gender
        )
        
        return jsonify({
            'message': 'Profile saved successfully',
            'age': age,
            'resting_hr': resting_hr,
            'weight': weight,
            'gender': gender
        })
    except Exception as e:
        print(f"Error saving profile: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(runs_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(admin_bp)

# Add a health check endpoint
@app.route('/api/health')
def health_check():
    try:
        return jsonify({
            'status': 'ok',
            'environment': env,
            'database_type': 'SQLAlchemy' if hasattr(db, 'use_sqlalchemy') and db.use_sqlalchemy else 'SQLite',
            'has_flask_cors': has_flask_cors
        })
    except Exception as e:
        error_msg = handle_exception(e)
        return jsonify({'error': error_msg}), 500

# Add a admin-only endpoint to list users (temporary for debugging)
@app.route('/admin/list-accounts', methods=['GET'])
def admin_list_accounts():
    try:
        # Check for admin authorization (only allow admin user)
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
            
        # Get the current user's info
        user_id = session['user_id']
        
        # Verify this is the admin user
        if user_id != 1:  # Admin user ID is typically 1
            return jsonify({'error': 'Not authorized'}), 403
            
        # Get all users from the database
        if db.use_sqlalchemy:
            with db.engine.connect() as conn:
                # For PostgreSQL (SQLAlchemy)
                result = conn.execute(
                    select([db.users.c.id, db.users.c.username, db.users.c.created_at])
                )
                users = [
                    {"id": row[0], "username": row[1], "created_at": row[2]} 
                    for row in result
                ]
                
                # Also get profile data
                profiles = {}
                for user in users:
                    profile_result = conn.execute(
                        select([db.profile]).where(db.profile.c.user_id == user["id"])
                    )
                    profile = profile_result.fetchone()
                    if profile:
                        profiles[user["id"]] = {
                            "age": profile.age,
                            "resting_hr": profile.resting_hr,
                            "weight": profile.weight,
                            "gender": "Male" if profile.gender == 1 else "Female"
                        }
                
                # Add run counts
                for user in users:
                    run_count_result = conn.execute(
                        select([func.count()]).select_from(db.runs).where(db.runs.c.user_id == user["id"])
                    )
                    user["run_count"] = run_count_result.scalar() or 0
                    user["profile"] = profiles.get(user["id"], {})
        else:
            # For SQLite
            with sqlite3.connect('runs.db') as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all users
                cursor.execute('''
                    SELECT u.id, u.username, u.created_at
                    FROM users u
                    ORDER BY u.id
                ''')
                users = [dict(row) for row in cursor.fetchall()]
                
                # Get profiles and run counts
                for user in users:
                    # Get profile
                    cursor.execute('''
                        SELECT age, resting_hr, weight, gender
                        FROM profile
                        WHERE user_id = ?
                    ''', (user["id"],))
                    profile = cursor.fetchone()
                    if profile:
                        user["profile"] = {
                            "age": profile["age"],
                            "resting_hr": profile["resting_hr"],
                            "weight": profile["weight"],
                            "gender": "Male" if profile["gender"] == 1 else "Female"
                        }
                    else:
                        user["profile"] = {}
                    
                    # Get run count
                    cursor.execute('SELECT COUNT(*) FROM runs WHERE user_id = ?', (user["id"],))
                    user["run_count"] = cursor.fetchone()[0]
        
        return jsonify({
            "users": users,
            "environment": env,
            "database_type": "SQLAlchemy" if db.use_sqlalchemy else "SQLite",
            "message": "This is a temporary endpoint for debugging purposes. Please remove in production."
        })
        
    except Exception as e:
        error_msg = handle_exception(e)
        return jsonify({'error': error_msg}), 500

# Start server if run directly
if __name__ == '__main__':
    print("Starting server on http://localhost:5001")
    app.run(
        debug=env == 'development',
        host='localhost',
        port=5001,
        ssl_context=None
    ) 