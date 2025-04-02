from flask import Blueprint, request, jsonify, session, abort, render_template, redirect, url_for, send_file
import traceback
from functools import wraps
from werkzeug.security import generate_password_hash
from sqlalchemy import select, func
from datetime import datetime
import shutil
import subprocess

# Import the database adapter
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from app.database_adapter import RunDatabaseAdapter

# Create the admin blueprint
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin', template_folder='../templates')
db = RunDatabaseAdapter()

# Admin-only decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized - Please log in'}), 401
            
        # Check if the user is admin (user_id = 1)
        if session['user_id'] != 1:
            return jsonify({'error': 'Forbidden - Admin access required'}), 403
            
        # User is admin, continue
        return f(*args, **kwargs)
    return decorated_function

# Login route specifically for admin
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        # Render login page
        return render_template('admin_login.html')
    else:
        # Process login
        try:
            # Handle both form data and JSON
            username = request.form.get('username')
            password = request.form.get('password')
            
            # If not form data, try JSON
            if not username or not password:
                try:
                    data = request.get_json()
                    if data:
                        username = data.get('username')
                        password = data.get('password')
                except:
                    pass
            
            if not username or not password:
                if request.content_type and 'application/json' in request.content_type:
                    return jsonify({'error': 'Username and password required'}), 400
                return render_template('admin_login.html', error='Username and password required')
                
            # Only allow 'admin' username for admin login
            if username != 'admin':
                if request.content_type and 'application/json' in request.content_type:
                    return jsonify({'error': 'Invalid admin credentials'}), 401
                return render_template('admin_login.html', error='Invalid admin credentials')
                
            # Verify credentials
            user_id = db.verify_user(username, password)
            if not user_id or user_id != 1:
                if request.content_type and 'application/json' in request.content_type:
                    return jsonify({'error': 'Invalid admin credentials'}), 401
                return render_template('admin_login.html', error='Invalid admin credentials')
                
            # Set session
            session['user_id'] = user_id
            session['is_admin'] = True
            
            # Redirect to dashboard if form submission, otherwise return JSON
            if request.content_type and 'application/json' in request.content_type:
                return jsonify({'success': True, 'redirect': '/admin/dashboard'})
            else:
                return redirect(url_for('admin_bp.dashboard'))
        except Exception as e:
            print(f"Admin login error: {str(e)}")
            traceback.print_exc()
            if request.content_type and 'application/json' in request.content_type:
                return jsonify({'error': str(e)}), 500
            return render_template('admin_login.html', error=f'Login error: {str(e)}')

# Admin dashboard
@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    try:
        # Get all users with their profile information and run counts
        users = get_all_users_with_data()
        
        # Debug user data
        print(f"\n=== ADMIN DASHBOARD DEBUG ===")
        print(f"Users data type: {type(users)}")
        print(f"Users count: {len(users) if users else 0}")
        if users and len(users) > 0:
            print(f"Sample user: {users[0]}")
        else:
            print("No users found. Fallback to direct database access.")
            
            # Fallback to direct database query
            try:
                import sqlite3
                db_path = os.environ.get('DATABASE_PATH', 'runs.db')
                print(f"Attempting direct database access at: {db_path}")
                
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Get all users, including admin
                    cursor.execute('''
                        SELECT id, username, created_at 
                        FROM users 
                        ORDER BY id
                    ''')
                    users = [dict(row) for row in cursor.fetchall()]
                    
                    # Get profile and run count for each user
                    for user in users:
                        # Get profile
                        cursor.execute('SELECT age, resting_hr, weight, gender FROM profile WHERE user_id = ?', 
                                      (user['id'],))
                        profile = cursor.fetchone()
                        if profile:
                            user['profile'] = dict(profile)
                        else:
                            user['profile'] = {}
                            
                        # Get run count
                        cursor.execute('SELECT COUNT(*) FROM runs WHERE user_id = ?', (user['id'],))
                        user['run_count'] = cursor.fetchone()[0]
                    
                    print(f"Direct database access found {len(users)} users")
            except Exception as e:
                print(f"Error in fallback database access: {e}")
                # If all else fails, return a minimal admin user
                users = [{
                    'id': 1,
                    'username': 'admin',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'profile': {'age': 0, 'resting_hr': 0, 'weight': 70, 'gender': 1},
                    'run_count': 0
                }]
                print("Using hardcoded admin user as last resort")
        
        return render_template('admin_dashboard.html', users=users or [], now=datetime.now)
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# API endpoint to get all users with their data
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    try:
        users = get_all_users_with_data()
        return jsonify({'users': users})
    except Exception as e:
        print(f"Error getting users: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Reset a user's password
@admin_bp.route('/reset-password/<int:user_id>', methods=['POST'])
@admin_required
def reset_password(user_id):
    try:
        data = request.json or {}
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({'error': 'New password is required'}), 400
            
        # Don't allow resetting admin password through this route for security
        if user_id == 1:
            return jsonify({'error': 'Cannot reset admin password through this route'}), 403
            
        # Set the new password
        if db.admin_reset_password(user_id, new_password):
            return jsonify({'success': True, 'message': f'Password for user {user_id} reset successfully'})
        else:
            return jsonify({'error': f'Failed to reset password for user {user_id}'}), 500
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Delete a user account - Fixed to properly handle user deletion
@admin_bp.route('/delete-user/<int:user_id>', methods=['POST', 'DELETE'])
@admin_required
def delete_user(user_id):
    try:
        print(f"Admin attempting to delete user {user_id}")
        
        # Don't allow deleting admin account
        if user_id == 1:
            print("Attempt to delete admin account denied")
            return jsonify({'error': 'Cannot delete admin account'}), 403
            
        # Delete the user
        success = db.delete_user(user_id)
        if success:
            print(f"User {user_id} successfully deleted by admin")
            return jsonify({'success': True, 'message': f'User {user_id} deleted successfully'})
        else:
            print(f"Failed to delete user {user_id}")
            return jsonify({'error': f'Failed to delete user {user_id}'}), 500
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Logout from admin
@admin_bp.route('/logout', methods=['GET', 'POST'])
def admin_logout():
    # Clear session
    session.pop('user_id', None)
    session.pop('is_admin', None)
    
    # Redirect to login page
    return redirect(url_for('admin_bp.admin_login'))

# Helper function to get all users with their data
def get_all_users_with_data():
    print("\n=== RETRIEVING ALL USERS WITH DATA ===")
    
    try:
        # Try direct SQLite connection with the correct database path
        db_path = os.environ.get('DATABASE_PATH', 'runs.db')
        print(f"Using database at: {db_path}")
        
        # Check if the database exists
        if not os.path.exists(db_path):
            print(f"WARNING: Database not found at {db_path}")
            # Try alternate locations
            alternate_paths = [
                'runs.db',
                '../runs.db',
                './runs.db',
                '/opt/render/data/runs.db',
                '/opt/render/project/src/backend/runs.db',
                '/opt/render/project/src/runs.db'
            ]
            
            for alt_path in alternate_paths:
                if os.path.exists(alt_path):
                    print(f"Found database at alternate location: {alt_path}")
                    db_path = alt_path
                    break
        
        if not os.path.exists(db_path):
            print(f"CRITICAL: No database found at any location!")
            return []
            
        # Connect to the database
        print(f"Connecting to database at: {db_path}")
        import sqlite3
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all users
            cursor.execute('''
                SELECT id, username, created_at
                FROM users
                ORDER BY id
            ''')
            users = [dict(row) for row in cursor.fetchall()]
            print(f"Found {len(users)} users with direct SQLite connection")
            
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
                count_result = cursor.fetchone()
                user["run_count"] = count_result[0] if count_result else 0
        
        print(f"Total users retrieved: {len(users)}")
        if users:
            print(f"Sample user data: {users[0]}")
        return users
    except Exception as e:
        print(f"ERROR retrieving users: {str(e)}")
        traceback.print_exc()
        
        # Create minimal admin user as fallback
        try:
            fallback_users = [{
                'id': 1,
                'username': 'admin',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile': {'age': 0, 'resting_hr': 0, 'weight': 70, 'gender': 1},
                'run_count': 0
            }]
            print("Created fallback admin user")
            return fallback_users
        except:
            return []

# Database management routes
@admin_bp.route('/db_upload', methods=['POST'])
@admin_required
def db_upload():
    """Upload a database file to the server"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Validate file is a SQLite database
        if not file.filename.endswith('.db'):
            return jsonify({'error': 'File must be a SQLite database (.db)'}), 400
            
        # Save to a temporary location
        upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploaded_runs.db')
        file.save(upload_path)
        
        file_size = os.path.getsize(upload_path)
        
        print(f"Database file uploaded successfully to {upload_path} ({file_size} bytes)")
        
        # Basic validation that this is a valid SQLite database with expected tables
        try:
            import sqlite3
            with sqlite3.connect(upload_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Check for essential tables
                required_tables = ['users', 'profile', 'runs']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    os.remove(upload_path)  # Delete invalid file
                    return jsonify({
                        'error': f'Invalid database structure. Missing tables: {", ".join(missing_tables)}'
                    }), 400
                
                # Check user count
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                
                # Check run count
                cursor.execute("SELECT COUNT(*) FROM runs")
                run_count = cursor.fetchone()[0]
                
                print(f"Validated database: {user_count} users, {run_count} runs")
        except Exception as e:
            os.remove(upload_path)  # Delete invalid file
            return jsonify({'error': f'Invalid SQLite database: {str(e)}'}), 400
        
        return jsonify({
            'message': 'Database file uploaded successfully',
            'path': upload_path,
            'size': file_size,
            'user_count': user_count,
            'run_count': run_count
        })
    except Exception as e:
        print(f"Error uploading database: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/db_restore', methods=['POST'])
@admin_required
def db_restore():
    """Restore the database from the uploaded file"""
    try:
        uploaded_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploaded_runs.db')
        
        if not os.path.exists(uploaded_db):
            return jsonify({'error': 'No uploaded database found. Please upload a database first.'}), 400
        
        # Get the target database path
        db_path = os.environ.get('DATABASE_PATH')
        if not db_path:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'runs.db')
            
        print(f"Restoring database from {uploaded_db} to {db_path}")
        
        # Create a backup of the current database
        backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            print(f"Backup created at {backup_path}")
        
        # Copy the uploaded database to the target location
        shutil.copy2(uploaded_db, db_path)
        
        # Verify the copy was successful
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            print(f"Database restored successfully. Size: {db_size} bytes")
            
            # Run the restore script if it exists (Render-specific)
            restore_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'restore_db_auto.sh')
            if os.path.exists(restore_script):
                try:
                    # Make sure it's executable
                    subprocess.run(['chmod', '+x', restore_script], check=True)
                    # Run the script
                    result = subprocess.run([restore_script], 
                                           capture_output=True, 
                                           text=True,
                                           check=False)
                    print(f"Restore script output: {result.stdout}")
                    if result.stderr:
                        print(f"Restore script errors: {result.stderr}")
                except Exception as e:
                    print(f"Error running restore script: {str(e)}")
            
            return jsonify({
                'message': 'Database restored successfully',
                'backup_path': backup_path,
                'size': db_size
            })
        else:
            return jsonify({'error': 'Failed to restore database. Target file not found after copy.'}), 500
    except Exception as e:
        print(f"Error restoring database: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/db_backup', methods=['POST'])
@admin_required
def db_backup():
    """Create a backup of the current database"""
    try:
        # Get the current database path
        db_path = os.environ.get('DATABASE_PATH')
        if not db_path:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'runs.db')
        
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found at expected location'}), 404
        
        # Create a backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"gpx4u_backup_{timestamp}.db"
        backup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', backup_filename)
        
        # Create static directory if it doesn't exist
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Copy the database to the backup location
        shutil.copy2(db_path, backup_path)
        
        if os.path.exists(backup_path):
            backup_size = os.path.getsize(backup_path)
            print(f"Database backup created at {backup_path} ({backup_size} bytes)")
            
            return jsonify({
                'message': 'Database backup created successfully',
                'filename': backup_filename,
                'path': backup_path,
                'size': backup_size
            })
        else:
            return jsonify({'error': 'Failed to create backup. Backup file not found after copy.'}), 500
    except Exception as e:
        print(f"Error creating database backup: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/db_download/<filename>', methods=['GET'])
@admin_required
def db_download(filename):
    """Download a database backup file"""
    try:
        # Validate filename to prevent directory traversal
        if '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
            
        # Only allow .db files
        if not filename.endswith('.db'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Construct the file path
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        # Return the file as an attachment
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        print(f"Error downloading backup: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Static upload page route as a fallback
@admin_bp.route('/db_upload_page', methods=['GET'])
@admin_required
def db_upload_page():
    """Serve the database upload page directly"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GPX4U Database Upload</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    .card {
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .form-group {
      margin-bottom: 15px;
    }
    label {
      display: block;
      margin-bottom: 5px;
      font-weight: bold;
    }
    button {
      background-color: #4CAF50;
      color: white;
      padding: 10px 15px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    button:hover {
      background-color: #45a049;
    }
    .alert {
      padding: 15px;
      margin-bottom: 20px;
      border-radius: 4px;
    }
    .alert-success {
      background-color: #dff0d8;
      color: #3c763d;
      border: 1px solid #d6e9c6;
    }
    .alert-danger {
      background-color: #f2dede;
      color: #a94442;
      border: 1px solid #ebccd1;
    }
    .hidden {
      display: none;
    }
    #status {
      margin-top: 20px;
    }
  </style>
</head>
<body>
  <h1>GPX4U Database Upload</h1>
  
  <div class="card">
    <h2>Upload Database File</h2>
    <p>Use this form to upload your SQLite database file to restore your data.</p>
    
    <form id="uploadForm" enctype="multipart/form-data">
      <div class="form-group">
        <label for="file">Select Database File:</label>
        <input type="file" id="file" name="file" accept=".db" required>
      </div>
      
      <button type="submit">Upload Database</button>
    </form>
    
    <div id="status" class="hidden"></div>
  </div>
  
  <div class="card">
    <h2>Next Steps</h2>
    <p>After uploading your database:</p>
    <ol>
      <li>Click the "Yes, Restore Now" button when prompted, or</li>
      <li>Go to the admin dashboard to complete the restoration</li>
    </ol>
  </div>

  <script>
    document.getElementById('uploadForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const fileInput = document.getElementById('file');
      const file = fileInput.files[0];
      const statusDiv = document.getElementById('status');
      
      if (!file) {
        statusDiv.className = 'alert alert-danger';
        statusDiv.textContent = 'Please select a file to upload.';
        statusDiv.classList.remove('hidden');
        return;
      }
      
      const formData = new FormData();
      formData.append('file', file);
      
      statusDiv.className = 'alert';
      statusDiv.textContent = 'Uploading...';
      statusDiv.classList.remove('hidden');
      
      try {
        const response = await fetch('/admin/db_upload', {
          method: 'POST',
          body: formData,
          credentials: 'include'
        });
        
        const result = await response.json();
        
        if (response.ok) {
          statusDiv.className = 'alert alert-success';
          statusDiv.innerHTML = `
            <strong>Success!</strong> Database uploaded successfully.<br>
            Location: ${result.path}<br>
            Size: ${formatBytes(result.size)}<br>
            Users: ${result.user_count}<br>
            Runs: ${result.run_count}<br>
            <hr>
            <p>Would you like to restore this database now?</p>
            <button id="restoreNowBtn" class="btn btn-success">Yes, Restore Now</button>
            <button id="cancelRestoreBtn" class="btn btn-secondary">Cancel</button>
          `;
          
          document.getElementById('restoreNowBtn').addEventListener('click', async function() {
            statusDiv.innerHTML = '<div class="alert">Restoring database... This may take a moment.</div>';
            
            try {
              const restoreResponse = await fetch('/admin/db_restore', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                credentials: 'include'
              });
              
              const restoreResult = await restoreResponse.json();
              
              if (restoreResponse.ok) {
                statusDiv.innerHTML = `
                  <div class="alert alert-success">
                    <strong>Database restored successfully!</strong><br>
                    <p>Return to <a href="/admin/dashboard">Admin Dashboard</a> or reload in 3 seconds...</p>
                  </div>
                `;
                
                setTimeout(() => {
                  window.location.reload();
                }, 3000);
              } else {
                throw new Error(restoreResult.error || 'Restore failed');
              }
            } catch (error) {
              statusDiv.innerHTML = `<div class="alert alert-danger">Error during restore: ${error.message}</div>`;
            }
          });
          
          document.getElementById('cancelRestoreBtn').addEventListener('click', function() {
            statusDiv.innerHTML = '<div class="alert">Restore cancelled. You can still restore from the Admin Dashboard.</div>';
          });
        } else {
          statusDiv.className = 'alert alert-danger';
          statusDiv.textContent = `Error: ${result.error || 'Upload failed'}`;
        }
      } catch (error) {
        statusDiv.className = 'alert alert-danger';
        statusDiv.textContent = `Error: ${error.message || 'Unknown error occurred'}`;
      }
    });
    
    function formatBytes(bytes, decimals = 2) {
      if (bytes === 0) return '0 Bytes';
      
      const k = 1024;
      const dm = decimals < 0 ? 0 : decimals;
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      
      return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
  </script>
</body>
</html>
    """
    return html_content 