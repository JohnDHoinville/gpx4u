from flask import Blueprint, request, jsonify, session, abort, render_template, redirect, url_for
import traceback
from functools import wraps
from werkzeug.security import generate_password_hash
from sqlalchemy import select, func
from datetime import datetime

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
        return render_template('admin_dashboard.html', users=users, now=datetime.now)
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
        data = request.json or request.form
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

# Delete a user account
@admin_bp.route('/delete-user/<int:user_id>', methods=['POST', 'DELETE'])
@admin_required
def delete_user(user_id):
    try:
        # Don't allow deleting admin account
        if user_id == 1:
            return jsonify({'error': 'Cannot delete admin account'}), 403
            
        # Delete the user
        if db.delete_user(user_id):
            return jsonify({'success': True, 'message': f'User {user_id} deleted successfully'})
        else:
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
    users = []
    
    try:
        # Try direct SQLite connection regardless of db.use_sqlalchemy
        print("Using direct SQLite connection to get users")
        import sqlite3
        with sqlite3.connect('runs.db') as conn:
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
                user["run_count"] = cursor.fetchone()[0]
        
        print(f"Total users retrieved: {len(users)}")
        if users:
            print(f"Sample user data: {users[0]}")
        return users
    except Exception as e:
        print(f"ERROR retrieving users: {str(e)}")
        traceback.print_exc()
        return [] 