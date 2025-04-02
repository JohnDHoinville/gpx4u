#!/usr/bin/env python3
"""
Database diagnostic script for GPX4U application.
This script checks for database files in various locations, 
analyzes them, and helps diagnose issues with database access.
"""

import os
import sys
import sqlite3
import traceback
from datetime import datetime

# List of potential database paths to check
DB_PATHS = [
    '/opt/render/data/runs.db',  # Render.com persistent storage
    os.environ.get('DATABASE_PATH'),  # From environment variable
    'runs.db',  # Current directory
    './runs.db',  # Explicit current directory
    '../runs.db',  # Parent directory
    'backend/runs.db',  # Backend subdirectory
    '/tmp/runs.db',  # Temporary directory
]

# Filter out None paths
DB_PATHS = [path for path in DB_PATHS if path]

def check_directory(path):
    """Check if a directory exists and is writable"""
    dir_path = os.path.dirname(os.path.abspath(path))
    
    # If we're dealing with a path without a directory part
    if not dir_path:
        dir_path = os.getcwd()
    
    result = {
        'exists': os.path.exists(dir_path),
        'path': dir_path,
        'writable': False,
        'readable': False,
        'error': None
    }
    
    if result['exists']:
        try:
            # Check read permission
            result['readable'] = os.access(dir_path, os.R_OK)
            
            # Check write permission
            result['writable'] = os.access(dir_path, os.W_OK)
            
            # Get directory info
            result['stat'] = os.stat(dir_path)
        except Exception as e:
            result['error'] = str(e)
    
    return result

def check_database_file(path):
    """Check if a database file exists and analyze it"""
    result = {
        'exists': os.path.exists(path),
        'path': path,
        'writable': False,
        'readable': False,
        'size': 0,
        'error': None,
        'tables': [],
        'counts': {},
        'is_valid_db': False
    }
    
    if result['exists']:
        try:
            # Check read permission
            result['readable'] = os.access(path, os.R_OK)
            
            # Check write permission
            result['writable'] = os.access(path, os.W_OK)
            
            # Get file size
            result['size'] = os.path.getsize(path)
            
            # Get file info
            result['stat'] = os.stat(path)
            
            # Try to open it as a database
            try:
                with sqlite3.connect(path) as conn:
                    cursor = conn.cursor()
                    
                    # Get tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    result['tables'] = [row[0] for row in cursor.fetchall()]
                    result['is_valid_db'] = True
                    
                    # Check for expected tables
                    expected_tables = ['users', 'profile', 'runs']
                    result['missing_tables'] = [table for table in expected_tables if table not in result['tables']]
                    
                    # Get counts for expected tables
                    for table in result['tables']:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            result['counts'][table] = cursor.fetchone()[0]
                        except:
                            result['counts'][table] = "ERROR"
                    
                    # Try to get schema for each table
                    result['schema'] = {}
                    for table in result['tables']:
                        try:
                            cursor.execute(f"PRAGMA table_info({table})")
                            result['schema'][table] = cursor.fetchall()
                        except:
                            result['schema'][table] = "ERROR"
            except Exception as e:
                result['db_error'] = str(e)
        except Exception as e:
            result['error'] = str(e)
    
    return result

def can_create_database(path):
    """Check if we can create a new database at the specified path"""
    result = {
        'path': path,
        'can_create': False,
        'error': None
    }
    
    # Check if directory exists and is writable
    dir_check = check_directory(path)
    if not dir_check['exists'] or not dir_check['writable']:
        result['error'] = f"Directory {dir_check['path']} does not exist or is not writable"
        return result
    
    # Check if a file already exists (we don't want to overwrite)
    if os.path.exists(path):
        result['error'] = f"File already exists at {path}"
        return result
    
    # Try to create a test database
    try:
        test_path = f"{path}.test"
        with sqlite3.connect(test_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.commit()
        
        # Clean up the test file
        os.remove(test_path)
        result['can_create'] = True
    except Exception as e:
        result['error'] = str(e)
    
    return result

def print_result(title, result):
    """Pretty print a result dictionary"""
    print(f"\n== {title} ==")
    for key, value in result.items():
        if key == 'stat':
            # Format stat result
            print(f"  {key}:")
            print(f"    uid: {value.st_uid}, gid: {value.st_gid}")
            print(f"    mode: {value.st_mode}")
            print(f"    created: {datetime.fromtimestamp(value.st_ctime)}")
            print(f"    modified: {datetime.fromtimestamp(value.st_mtime)}")
        elif key == 'schema':
            # Format schema
            print(f"  {key}:")
            for table, schema in value.items():
                print(f"    {table}:")
                if schema == "ERROR":
                    print(f"      ERROR")
                else:
                    for column in schema:
                        print(f"      {column}")
        elif key == 'tables':
            print(f"  {key}: {', '.join(value)}")
        elif key == 'counts':
            print(f"  {key}:")
            for table, count in value.items():
                print(f"    {table}: {count}")
        elif key == 'missing_tables':
            if value:
                print(f"  {key}: {', '.join(value)}")
            else:
                print(f"  {key}: None")
        else:
            print(f"  {key}: {value}")

def main():
    """Main function to check all database paths"""
    print(f"GPX4U Database Diagnostic Tool - {datetime.now()}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    print(f"Environment variables:")
    print(f"  DATABASE_PATH: {os.environ.get('DATABASE_PATH')}")
    print(f"  FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    
    # Check if we're on Render
    is_render = os.path.exists('/opt/render')
    print(f"Running on Render.com: {is_render}")
    
    # Check all paths
    print("\nChecking all possible database paths:")
    for i, path in enumerate(DB_PATHS):
        print(f"\n[{i+1}/{len(DB_PATHS)}] Checking path: {path}")
        
        # Check directory
        dir_result = check_directory(path)
        print_result(f"Directory for {path}", dir_result)
        
        # Check database file
        db_result = check_database_file(path)
        print_result(f"Database file at {path}", db_result)
        
        # Check if we can create a database here
        if not db_result['exists']:
            create_result = can_create_database(path)
            print_result(f"Can create database at {path}", create_result)
    
    # Print summary
    print("\n== Summary ==")
    print("Valid databases found:")
    valid_dbs = [path for path in DB_PATHS if check_database_file(path)['is_valid_db']]
    
    if valid_dbs:
        for path in valid_dbs:
            result = check_database_file(path)
            print(f"  - {path} ({result['size']} bytes)")
            print(f"    Tables: {', '.join(result['tables'])}")
            if 'users' in result['counts']:
                print(f"    Users: {result['counts']['users']}")
            if 'runs' in result['counts']:
                print(f"    Runs: {result['counts']['runs']}")
    else:
        print("  None")
    
    print("\nWritable locations for new database:")
    writable_dirs = [path for path in DB_PATHS if check_directory(path)['writable']]
    
    if writable_dirs:
        for path in writable_dirs:
            print(f"  - {path}")
    else:
        print("  None")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error running diagnostic: {e}")
        traceback.print_exc()
        sys.exit(1) 