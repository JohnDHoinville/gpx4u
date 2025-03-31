#!/usr/bin/env python
from flask import Flask, request, jsonify, session
import sqlite3
from werkzeug.security import check_password_hash
import os
import traceback

app = Flask(__name__)
app.secret_key = 'test-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'

@app.route('/test-login', methods=['POST'])
def test_login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        print(f"\n=== TEST LOGIN ATTEMPT ===")
        print(f"Username: {username}")
        print(f"Password: {password[:1]}{'*' * (len(password)-2)}{password[-1:] if len(password) > 1 else ''}")
        
        # Check session before login
        print(f"Session before login: {dict(session)}")
        
        # Verify user in database
        user_id = verify_user(username, password)
        
        if user_id:
            # Set session variables
            session['user_id'] = user_id
            session['logged_in'] = True
            session.modified = True
            
            # Debug session after login
            print(f"Session after login: {dict(session)}")
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user_id': user_id,
                'session': dict(session)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
    except Exception as e:
        print(f"Error in test login: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def verify_user(username, password):
    """Verify user credentials against database"""
    db_name = 'runs.db'
    
    if not os.path.exists(db_name):
        print(f"Database file {db_name} not found.")
        return None
    
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            if not user:
                print(f"User '{username}' not found")
                return None
                
            user_id, password_hash = user
            print(f"Found user ID: {user_id}")
            print(f"Hash method: {password_hash.split('$')[0] if '$' in password_hash else 'unknown'}")
            
            # Try password verification
            try:
                result = check_password_hash(password_hash, password)
                print(f"Password check result: {'Success' if result else 'Failed'}")
                
                if result:
                    print(f"Authentication successful for user: {username}")
                    return user_id
                else:
                    print(f"Password verification failed for user: {username}")
            except Exception as e:
                print(f"Error in password verification: {e}")
                traceback.print_exc()
                
            return None
    except Exception as e:
        print(f"Error verifying user: {e}")
        traceback.print_exc()
        return None

@app.route('/test-session', methods=['GET'])
def test_session():
    """Test if the session is working properly"""
    return jsonify({
        'session': dict(session),
        'has_user_id': 'user_id' in session,
        'user_id': session.get('user_id')
    })

if __name__ == '__main__':
    app.run(debug=True, port=5002) 