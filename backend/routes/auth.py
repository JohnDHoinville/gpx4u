from flask import Blueprint, request, jsonify, session
import traceback
from app.database import RunDatabase
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

auth_bp = Blueprint('auth_bp', __name__)
db = RunDatabase()  # This will now use DATABASE_PATH from environment

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
            
        user_id = db.create_user(username, password)
        session['user_id'] = user_id
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
        })
    except Exception as e:
        print(f"Registration error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Username already exists'}), 400


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        print("\n=== LOGIN ATTEMPT ===")
        data = request.json
        username = data.get('username')
        password = data.get('password')
        print(f"Login attempt for user: {username}")
        
        # Add detailed debugging
        print(f"Password provided: {password[:1]}{'*' * (len(password)-2)}{password[-1:] if len(password) > 1 else ''}")
        
        # Special case for johndhoinville@gmail.com
        if username == "johndhoinville@gmail.com":
            print("SPECIAL LOGIN CASE for johndhoinville@gmail.com")
            
            # Check if password matches any of our override passwords
            if password == "password123" or password == "ilovesolden":
                # Get the user ID
                with sqlite3.connect('runs.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
                    user = cursor.fetchone()
                    
                    if user:
                        user_id = user[0]
                        print(f"OVERRIDE LOGIN: Setting session user_id to {user_id}")
                        
                        # Manually set session
                        session['user_id'] = user_id
                        session['logged_in'] = True
                        session.modified = True
                        
                        # Debug session 
                        print(f"Session after override login: {dict(session)}")
                        
                        return jsonify({
                            'message': 'Login successful (OVERRIDE)',
                            'user_id': user_id
                        })
                    else:
                        print("OVERRIDE FAILED: User not found in database")
            else:
                print(f"OVERRIDE FAILED: Password doesn't match override passwords (tried both 'password123' and 'ilovesolden')")
        
        # Check session before login
        print(f"Session before login: {dict(session)}")
        
        user_id = db.verify_user(username, password)
        print(f"Verify user result: {user_id}")
        
        if user_id:
            session['user_id'] = user_id
            session['logged_in'] = True  # Add an explicit logged_in flag
            session.modified = True  # Ensure session is saved
            
            # Debug session after login
            print(f"Session after login: {dict(session)}")
            print(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No session ID'}")
            
            response = jsonify({
                'message': 'Login successful',
                'user_id': user_id
            })
            
            print(f"Login successful for user: {username} (ID: {user_id})")
            print(f"Response: {response.get_data(as_text=True)}")
            print("=== END LOGIN ATTEMPT ===\n")
            return response
            
        print(f"Login failed: Invalid credentials for user: {username}")
        print("=== END LOGIN ATTEMPT ===\n")
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        traceback.print_exc()
        print("=== END LOGIN ATTEMPT (ERROR) ===\n")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    # Clear all session data
    session.clear()
    return jsonify({'message': 'Logged out successfully'})


@auth_bp.route('/auth/check', methods=['GET'])
def check_auth():
    print("Received auth check request")
    try:
        if 'user_id' in session:
            print(f"User {session['user_id']} is authenticated")
            return jsonify({
                'authenticated': True,
                'user_id': session['user_id']
            })
        print("No user in session")
        return jsonify({
            'authenticated': False,
            'user_id': None
        })
    except Exception as e:
        print(f"Auth check error: {str(e)}")
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500


@auth_bp.route('/auth/change-password', methods=['POST'])
def change_password():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Both current and new password required'}), 400
            
        if not db.update_password(session['user_id'], current_password, new_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
            
        return jsonify({'message': 'Password updated successfully'})
    except Exception as e:
        print(f"Password change error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/auth/login', methods=['OPTIONS'])
@auth_bp.route('/auth/register', methods=['OPTIONS'])
@auth_bp.route('/auth/logout', methods=['OPTIONS'])
@auth_bp.route('/auth/check', methods=['OPTIONS'])
def auth_options():
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept, Cookie')
    return response 