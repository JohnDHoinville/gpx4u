#!/usr/bin/env python
import os
import sqlite3
from werkzeug.security import generate_password_hash
import sys

def update_user_password(username, new_password, user_entered_password=None):
    """Update the password for a specific user"""
    db_name = 'runs.db'
    
    if not os.path.exists(db_name):
        print(f"Database file {db_name} not found.")
        return False
    
    try:
        # Use pbkdf2:sha256 method for better compatibility
        password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            
            # Verify the user exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            if not user:
                print(f"User '{username}' not found in the database.")
                return False
                
            # Update the password
            cursor.execute(
                'UPDATE users SET password_hash = ? WHERE username = ?',
                (password_hash, username)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"Password updated successfully for user '{username}'.")
                
                # If user provided their password, create an additional hash for that
                if user_entered_password:
                    user_password_hash = generate_password_hash(user_entered_password, method='pbkdf2:sha256')
                    print(f"Additional hash created for user-entered password.")
                    print(f"User password: {user_entered_password[:1]}{'*' * (len(user_entered_password)-2)}{user_entered_password[-1:]}")
                    print(f"To manually update in database: UPDATE users SET password_hash = '{user_password_hash}' WHERE username = '{username}';")
                
                return True
            else:
                print(f"Failed to update password for user '{username}'.")
                return False
            
    except Exception as e:
        print(f"Error updating password: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = "johndhoinville@gmail.com"  # Default to your account
    
    # Original password we set
    new_password = "password123"
    
    # Set this to the password you're actually trying to use
    user_entered_password = "ilovesolden"  # Based on your input mask i*********n
    
    update_user_password(username, new_password, user_entered_password) 