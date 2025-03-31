#!/usr/bin/env python
import os
import sqlite3
from werkzeug.security import check_password_hash
import sys

def test_login(username, password):
    """Test login functionality directly with the database"""
    db_name = 'runs.db'
    
    if not os.path.exists(db_name):
        print(f"Database file {db_name} not found.")
        return False
    
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            
            # Get the user
            cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            if not user:
                print(f"User '{username}' not found in the database.")
                return False
            
            user_id, password_hash = user
            
            # Check the password using different methods
            methods = ["plain", "check_password_hash"]
            for method in methods:
                if method == "plain":
                    print(f"\nMethod: Direct comparison of hashes")
                    print(f"Stored hash: {password_hash}")
                    # This is just for debugging - plain comparison won't work for secure hashes
                    print(f"Direct match would be: {password == password_hash}")
                    
                elif method == "check_password_hash":
                    print(f"\nMethod: check_password_hash")
                    try:
                        result = check_password_hash(password_hash, password)
                        print(f"Hash method: {password_hash.split('$')[0] if '$' in password_hash else 'unknown'}")
                        print(f"Result: {'Success' if result else 'Failed'}")
                        
                        if result:
                            print(f"\nLOGIN SUCCESSFUL!")
                            print(f"User ID: {user_id}")
                            return True
                    except Exception as e:
                        print(f"Error checking password: {e}")
            
            print("\nAll login methods failed.")
            return False
            
    except Exception as e:
        print(f"Error testing login: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    username = "johndhoinville@gmail.com"
    password = "password123"
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
    if len(sys.argv) > 2:
        password = sys.argv[2]
    
    print(f"Testing login for user: {username}")
    test_login(username, password) 