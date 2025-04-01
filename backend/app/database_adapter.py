import os
import json
from datetime import datetime
import traceback
from json import JSONEncoder
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Import SQLAlchemy for PostgreSQL support
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base

# Get configuration
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from config import config

# Environment
env = os.environ.get('FLASK_ENV', 'development')
CONFIG = config[env]

# Add a proper JSON encoder for Infinity values
class SafeJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)
        
    def encode(self, obj):
        # Pre-process the object to handle special values
        def handle_special_values(item):
            if isinstance(item, float):
                if item == float('inf') or item == float('Infinity'):
                    return "Infinity"
                if item == float('-inf') or item == float('-Infinity'):
                    return "-Infinity"
                if item != item:  # Check for NaN
                    return "NaN"
            elif isinstance(item, dict):
                return {k: handle_special_values(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [handle_special_values(i) for i in item]
            return item
            
        # Process the entire object tree
        processed_obj = handle_special_values(obj)
        return super().encode(processed_obj)

# Use this instead of the regular JSON encoder
def safe_json_dumps(obj):
    return json.dumps(obj, cls=SafeJSONEncoder)

# Database base class for SQLAlchemy
Base = declarative_base()

class RunDatabaseAdapter:
    """
    Database adapter with support for both SQLite and PostgreSQL
    """
    def __init__(self):
        # CRITICAL: Prioritize DATABASE_PATH environment variable
        # This ensures we use the persistent database path on Render.com
        db_path_env = os.environ.get('DATABASE_PATH')
        if db_path_env:
            print(f"Using DATABASE_PATH from environment: {db_path_env}")
            # For SQLite, construct the URI
            self.db_uri = f"sqlite:///{db_path_env}"
            self.db_name = db_path_env
            
            # Ensure the database directory exists
            db_dir = os.path.dirname(db_path_env)
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                    print(f"Created database directory: {db_dir}")
                except Exception as e:
                    print(f"Error creating directory: {e}")
                    
        # Otherwise, check for DATABASE_URL (PostgreSQL)
        elif os.environ.get('DATABASE_URL'):
            db_url = os.environ.get('DATABASE_URL')
            print(f"Using DATABASE_URL from environment: {db_url}")
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            self.db_uri = db_url
            self.db_name = None  # Not a file path for PostgreSQL
            
        # As a last resort, try CONFIG.DATABASE_URI
        else:
            try:
                # Handle the property vs attribute issue
                if hasattr(CONFIG, 'DATABASE_URI'):
                    if callable(getattr(CONFIG.__class__, 'DATABASE_URI', None)):
                        # It's a property, call it as a method
                        db_uri = CONFIG.DATABASE_URI
                        print(f"Using DATABASE_URI from config property: {db_uri}")
                    else:
                        # It's an attribute
                        db_uri = CONFIG.DATABASE_URI
                        print(f"Using DATABASE_URI from config attribute: {db_uri}")
                        
                    if db_uri and db_uri.startswith('sqlite:///'):
                        # Extract the file path for SQLite
                        self.db_name = db_uri[10:]
                        if not self.db_name.startswith('/'):
                            # Relative path - make absolute
                            self.db_name = os.path.abspath(self.db_name)
                        self.db_uri = db_uri
                    else:
                        self.db_uri = db_uri
                        self.db_name = None
                else:
                    # Default to SQLite in current directory
                    self.db_name = 'runs.db'
                    self.db_uri = f"sqlite:///{self.db_name}"
                    print(f"Using default database: {self.db_name}")
            except Exception as e:
                print(f"Error accessing config DATABASE_URI: {e}")
                # Default to SQLite in current directory
                self.db_name = 'runs.db'
                self.db_uri = f"sqlite:///{self.db_name}"
                print(f"Falling back to default database: {self.db_name}")
            
        print(f"Final Database URI: {self.db_uri}")
            
        # Check if we should use SQLAlchemy (for PostgreSQL)  
        if self.db_uri and isinstance(self.db_uri, str) and self.db_uri.startswith('postgresql'):
            try:
                print(f"Using PostgreSQL database")
                self.use_sqlalchemy = True
                # Try to create the engine - this will fail if psycopg2 is not installed
                self.engine = create_engine(self.db_uri)
                self.metadata = MetaData()
                self._setup_sqlalchemy_tables()
            except Exception as e:
                print(f"Error setting up PostgreSQL connection: {str(e)}")
                traceback.print_exc()
                # Fall back to SQLite
                print("Unable to use PostgreSQL, falling back to SQLite")
                self.use_sqlalchemy = False
                if not self.db_name:
                    self.db_name = os.path.abspath('runs.db')
                # Continue with SQLite setup below
        else:
            self.use_sqlalchemy = False
            
        # Ensure we have a valid database name for SQLite
        if not self.db_name:
            # Default to runs.db in current directory
            self.db_name = os.path.abspath('runs.db')
            print(f"Using default SQLite database path: {self.db_name}")
            
        # Make sure the directory exists
        db_dir = os.path.dirname(self.db_name)
        if db_dir and not os.path.exists(db_dir):
            try:
                print(f"Creating database directory: {db_dir}")
                os.makedirs(db_dir, exist_ok=True)
            except Exception as e:
                print(f"Error creating directory {db_dir}: {e}")
                # Fall back to current directory
                self.db_name = os.path.abspath('runs.db')
                print(f"Falling back to local database: {self.db_name}")
            
        # Check if a database exists at the target location
        if os.path.exists(self.db_name):
            print(f"Found existing database at: {self.db_name}")
            print(f"Database size: {os.path.getsize(self.db_name) / 1024:.2f} KB")
            self._ensure_sqlite_tables()
        else:
            # Only create a new database if one doesn't exist
            print(f"No database found at {self.db_name}. Creating new SQLite database.")
            try:
                self._init_sqlite_db()
            except Exception as e:
                print(f"Error initializing database: {e}")
                # Fall back to current directory if we can't write to the target location
                self.db_name = os.path.abspath('runs.db')
                print(f"Falling back to local database: {self.db_name}")
                self._init_sqlite_db()

    def _setup_sqlalchemy_tables(self):
        """Setup SQLAlchemy tables for PostgreSQL"""
        # Define tables
        self.users = Table(
            'users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('username', String, unique=True, nullable=False),
            Column('password_hash', String, nullable=False),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        self.profile = Table(
            'profile', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
            Column('age', Integer, default=0),
            Column('resting_hr', Integer, default=0),
            Column('weight', Float, default=70),
            Column('gender', Integer, default=1),  # 1 for male, 0 for female
            Column('updated_at', DateTime, default=datetime.utcnow)
        )
        
        self.runs = Table(
            'runs', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
            Column('date', String, nullable=False),
            Column('total_distance', Float),
            Column('avg_pace', Float),
            Column('avg_hr', Float),
            Column('pace_limit', Float),
            Column('data', Text),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Create tables in the database
        self.metadata.create_all(self.engine)
        
        # Create default admin user if needed
        with self.engine.connect() as conn:
            result = conn.execute(select(self.users.c.id).where(self.users.c.username == 'admin'))
            user = result.fetchone()
            
            if not user:
                # Create admin user
                password_hash = generate_password_hash('admin123')
                result = conn.execute(
                    insert(self.users).values(
                        username='admin', 
                        password_hash=password_hash
                    )
                )
                user_id = result.inserted_primary_key[0]
                
                # Create admin profile
                conn.execute(
                    insert(self.profile).values(
                        user_id=user_id, 
                        age=0, 
                        resting_hr=0
                    )
                )
                conn.commit()
                print("Created default admin user (username: admin, password: admin123)")

    def _init_sqlite_db(self):
        """Initialize SQLite database"""
        # Check if we should preserve existing database
        if os.environ.get('PRESERVE_DATABASE', 'true').lower() == 'true' and os.path.exists(self.db_name):
            print(f"PRESERVE_DATABASE flag is set - not modifying existing database at {self.db_name}")
            return
            
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Add users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create profile table with user_id
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    age INTEGER DEFAULT 0,
                    resting_hr INTEGER DEFAULT 0,
                    weight REAL DEFAULT 70,
                    gender INTEGER DEFAULT 1,  /* 1 for male, 0 for female */
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # Create runs table with all required columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    total_distance REAL,
                    avg_pace REAL,
                    avg_hr REAL,
                    pace_limit REAL,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()

            # Check if we need to create default admin user
            cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
            if not cursor.fetchone():
                password_hash = generate_password_hash('admin123')
                cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                             ('admin', password_hash))
                user_id = cursor.lastrowid
                cursor.execute('INSERT INTO profile (user_id, age, resting_hr) VALUES (?, 0, 0)',
                             (user_id,))
                conn.commit()
                print("Created default admin user (username: admin, password: admin123)")

    def _ensure_sqlite_tables(self):
        """Ensure all required tables exist in SQLite without recreating the database"""
        # Check if we should preserve existing database - in production, don't modify schema
        preserve_db = os.environ.get('PRESERVE_DATABASE', 'false').lower() == 'true'
        is_production = os.environ.get('FLASK_ENV', '') == 'production'
        
        if preserve_db and is_production:
            print(f"PRESERVE_DATABASE flag is set in production - not modifying database schema")
            print(f"Database at {self.db_name} will be used as-is")
            return
            
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Check if pace_limit column exists
            try:
                cursor.execute('SELECT pace_limit FROM runs LIMIT 1')
            except sqlite3.OperationalError:
                print("Adding pace_limit column to runs table")
                cursor.execute('ALTER TABLE runs ADD COLUMN pace_limit REAL')
                conn.commit()
            
            # Check if we need to add new columns
            try:
                cursor.execute('SELECT weight, gender FROM profile LIMIT 1')
            except sqlite3.OperationalError:
                print("Adding weight and gender columns to profile table")
                cursor.execute('ALTER TABLE profile ADD COLUMN weight REAL DEFAULT 70')
                cursor.execute('ALTER TABLE profile ADD COLUMN gender INTEGER DEFAULT 1')
                conn.commit()

    # The rest of the methods should be adapted to work with both SQLite and SQLAlchemy
    # Implementation follows the same pattern: check self.use_sqlalchemy and call
    # the appropriate method for SQLite or PostgreSQL
    
    def save_run(self, user_id, run_data):
        """Save run data for a user"""
        try:
            print("Saving run data for user:", user_id)
            
            # Extract values from run_data
            data_obj = run_data.get('data', {})
            if isinstance(data_obj, str):
                data_obj = json.loads(data_obj)
            
            # Calculate total time for average pace
            total_time = 0
            for segment in data_obj.get('fast_segments', []) + data_obj.get('slow_segments', []):
                if isinstance(segment, dict) and 'time_diff' in segment:
                    total_time += segment['time_diff']
            
            # Calculate average pace
            total_distance = data_obj.get('total_distance', 0)
            avg_pace = total_time / total_distance if total_distance > 0 else 0
            avg_hr = data_obj.get('avg_hr_all', 0)
            
            # Convert data to string if it's not already
            data_str = json.dumps(data_obj, cls=SafeJSONEncoder) if isinstance(data_obj, dict) else data_obj
            
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    result = conn.execute(
                        insert(self.runs).values(
                            user_id=user_id,
                            date=run_data['date'],
                            total_distance=total_distance,
                            avg_pace=avg_pace,
                            avg_hr=avg_hr,
                            data=data_str
                        )
                    )
                    conn.commit()
                    run_id = result.inserted_primary_key[0]
                    print(f"Successfully saved run {run_id} for user {user_id}")
                    return run_id
            else:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO runs (
                            user_id, 
                            date, 
                            total_distance, 
                            avg_pace, 
                            avg_hr, 
                            data
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        run_data['date'],
                        total_distance,
                        avg_pace,
                        avg_hr,
                        data_str
                    ))
                    conn.commit()
                    run_id = cursor.lastrowid
                    print(f"Successfully saved run {run_id} for user {user_id}")
                    return run_id
        except Exception as e:
            print(f"Error saving run: {str(e)}")
            traceback.print_exc()
            raise e
            
    # Add the rest of the methods here following the same pattern...
    # For brevity, only implementing a few core methods

    def get_run_by_id(self, run_id, user_id=None):
        """Get a run by ID, optionally filtered by user_id"""
        try:
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    query = select(self.runs).where(self.runs.c.id == run_id)
                    if user_id:
                        query = query.where(self.runs.c.user_id == user_id)
                    result = conn.execute(query)
                    run = result.fetchone()
                    
                    if run:
                        return {
                            'id': run.id,
                            'user_id': run.user_id,
                            'date': run.date,
                            'total_distance': run.total_distance,
                            'avg_pace': run.avg_pace,
                            'avg_hr': run.avg_hr,
                            'data': run.data
                        }
                    return None
            else:
                with sqlite3.connect(self.db_name) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    if user_id:
                        cursor.execute('SELECT * FROM runs WHERE id = ? AND user_id = ?', (run_id, user_id))
                    else:
                        cursor.execute('SELECT * FROM runs WHERE id = ?', (run_id,))
                        
                    run = cursor.fetchone()
                    if run:
                        return dict(run)
                    return None
        except Exception as e:
            print(f"Error getting run: {str(e)}")
            return None
            
    def get_profile(self, user_id):
        """Get a user's profile"""
        try:
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    result = conn.execute(
                        select(self.profile).where(self.profile.c.user_id == user_id)
                    )
                    profile = result.fetchone()
                    
                    if profile:
                        return {
                            'id': profile.id,
                            'user_id': profile.user_id,
                            'age': profile.age,
                            'resting_hr': profile.resting_hr,
                            'weight': profile.weight,
                            'gender': profile.gender
                        }
                    
                    # Create profile if it doesn't exist
                    result = conn.execute(
                        insert(self.profile).values(
                            user_id=user_id,
                            age=0,
                            resting_hr=0,
                            weight=70,
                            gender=1
                        )
                    )
                    conn.commit()
                    
                    return {
                        'id': result.inserted_primary_key[0],
                        'user_id': user_id,
                        'age': 0,
                        'resting_hr': 0,
                        'weight': 70,
                        'gender': 1
                    }
            else:
                with sqlite3.connect(self.db_name) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM profile WHERE user_id = ?', (user_id,))
                    profile = cursor.fetchone()
                    
                    if profile:
                        return dict(profile)
                    
                    # Create profile if it doesn't exist
                    cursor.execute(
                        'INSERT INTO profile (user_id, age, resting_hr, weight, gender) VALUES (?, 0, 0, 70, 1)',
                        (user_id,)
                    )
                    conn.commit()
                    profile_id = cursor.lastrowid
                    
                    return {
                        'id': profile_id,
                        'user_id': user_id,
                        'age': 0,
                        'resting_hr': 0,
                        'weight': 70,
                        'gender': 1
                    }
        except Exception as e:
            print(f"Error getting profile: {str(e)}")
            return {'age': 0, 'resting_hr': 0, 'weight': 70, 'gender': 1}
            
    def verify_user(self, username, password):
        """Verify user credentials"""
        try:
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    result = conn.execute(
                        select(self.users).where(self.users.c.username == username)
                    )
                    user = result.fetchone()
                    
                    if user and check_password_hash(user.password_hash, password):
                        return user.id
                    return None
            else:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
                    user = cursor.fetchone()
                    
                    if user and check_password_hash(user[1], password):
                        return user[0]
                    return None
        except Exception as e:
            print(f"Error verifying user: {str(e)}")
            return None

    def save_profile(self, user_id, age, resting_hr, weight=70, gender=1):
        """Save user profile information"""
        try:
            print(f"Saving profile for user {user_id}:")
            print(f"Age: {age}, Resting HR: {resting_hr}, Weight: {weight}, Gender: {gender}")
            
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    result = conn.execute(
                        update(self.profile)
                        .where(self.profile.c.user_id == user_id)
                        .values(
                            age=age,
                            resting_hr=resting_hr,
                            weight=weight,
                            gender=gender,
                            updated_at=datetime.utcnow()
                        )
                    )
                    conn.commit()
                    print("Profile saved successfully using SQLAlchemy")
                    return True
            else:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE profile 
                        SET age = ?, resting_hr = ?, weight = ?, gender = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE user_id = ?
                    ''', (age, resting_hr, weight, gender, user_id))
                    conn.commit()
                    print("Profile saved successfully using SQLite")
                    return True
                    
        except Exception as e:
            print(f"Error saving profile: {str(e)}")
            traceback.print_exc()
            raise e
            
    def admin_reset_password(self, user_id, new_password):
        """Reset a user's password (admin function, no current password required)"""
        try:
            print(f"Admin resetting password for user {user_id}")
            
            # Generate password hash
            password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    result = conn.execute(
                        update(self.users)
                        .where(self.users.c.id == user_id)
                        .values(password_hash=password_hash)
                    )
                    conn.commit()
                    success = result.rowcount > 0
                    print(f"Password reset {'successful' if success else 'failed'} using SQLAlchemy")
                    return success
            else:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE users 
                        SET password_hash = ? 
                        WHERE id = ?
                    ''', (password_hash, user_id))
                    conn.commit()
                    success = cursor.rowcount > 0
                    print(f"Password reset {'successful' if success else 'failed'} using SQLite")
                    return success
                    
        except Exception as e:
            print(f"Error resetting password: {str(e)}")
            traceback.print_exc()
            return False
            
    def delete_user(self, user_id):
        """Delete a user account and all associated data (admin function)"""
        try:
            print(f"DB Adapter: Deleting user {user_id}")
            
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    # Delete runs first
                    conn.execute(
                        delete(self.runs)
                        .where(self.runs.c.user_id == user_id)
                    )
                    
                    # Delete profile
                    conn.execute(
                        delete(self.profile)
                        .where(self.profile.c.user_id == user_id)
                    )
                    
                    # Delete user
                    result = conn.execute(
                        delete(self.users)
                        .where(self.users.c.id == user_id)
                    )
                    
                    conn.commit()
                    success = result.rowcount > 0
                    print(f"User deletion {'successful' if success else 'failed'} using SQLAlchemy")
                    return success
            else:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    
                    # Delete runs first
                    print(f"DB Adapter: Deleting runs for user {user_id}")
                    cursor.execute('DELETE FROM runs WHERE user_id = ?', (user_id,))
                    
                    # Delete profile
                    print(f"DB Adapter: Deleting profile for user {user_id}")
                    cursor.execute('DELETE FROM profile WHERE user_id = ?', (user_id,))
                    
                    # Delete user
                    print(f"DB Adapter: Deleting user entry for user {user_id}")
                    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                    
                    conn.commit()
                    success = cursor.rowcount > 0
                    print(f"User deletion {'successful' if success else 'failed'} using SQLite")
                    # Even if rowcount is 0 (no rows affected), consider it successful
                    # This prevents issues if the user was already deleted
                    return True
                    
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            traceback.print_exc()
            return False
    
    def delete_run(self, run_id):
        """Delete a run by ID"""
        try:
            print(f"Deleting run {run_id}")
            
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    result = conn.execute(
                        delete(self.runs)
                        .where(self.runs.c.id == run_id)
                    )
                    conn.commit()
                    success = result.rowcount > 0
                    print(f"Run deletion {'successful' if success else 'failed'} using SQLAlchemy")
                    return success
            else:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM runs WHERE id = ?', (run_id,))
                    conn.commit()
                    success = cursor.rowcount > 0
                    print(f"Run deletion {'successful' if success else 'failed'} using SQLite")
                    return success
                    
        except Exception as e:
            print(f"Error deleting run: {str(e)}")
            traceback.print_exc()
            return False 