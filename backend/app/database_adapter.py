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
        # Safely get the database URI
        try:
            # Get the actual string value from the CONFIG.DATABASE_URI
            db_uri_value = CONFIG.DATABASE_URI
            
            # Print debug information about the URI type
            print(f"DATABASE_URI type: {type(db_uri_value)}")
            
            if db_uri_value is not None:
                if isinstance(db_uri_value, str):
                    self.db_uri = db_uri_value
                else:
                    # If it's not a string, try to convert it
                    self.db_uri = str(db_uri_value)
                    print(f"Converted DATABASE_URI to string: {self.db_uri}")
            else:
                print("DATABASE_URI is None, defaulting to SQLite")
                self.db_uri = None
        except Exception as e:
            print(f"Error accessing DATABASE_URI: {e}")
            traceback.print_exc()
            self.db_uri = None
            
        print(f"Final Database URI: {self.db_uri}")
        
        # Check if we should use SQLAlchemy (for PostgreSQL)  
        if self.db_uri and isinstance(self.db_uri, str) and self.db_uri.startswith('postgresql'):
            print(f"Using PostgreSQL database: {self.db_uri}")
            self.use_sqlalchemy = True
            self.engine = create_engine(self.db_uri)
            self.metadata = MetaData()
            self._setup_sqlalchemy_tables()
        else:
            self.use_sqlalchemy = False
            self.db_name = 'runs.db'
            if not os.path.exists(self.db_name):
                print(f"Creating new SQLite database: {self.db_name}")
                self._init_sqlite_db()
            else:
                print(f"Using existing database: {self.db_name}")
                self._ensure_sqlite_tables()

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

            # Create default admin user
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
        """Save a user's profile information"""
        try:
            print(f"Saving profile for user {user_id}:")
            print(f"Age: {age}, Resting HR: {resting_hr}, Weight: {weight}, Gender: {gender}")
            
            if self.use_sqlalchemy:
                with self.engine.connect() as conn:
                    # Check if profile exists
                    result = conn.execute(
                        select(self.profile.c.id).where(self.profile.c.user_id == user_id)
                    )
                    profile = result.fetchone()
                    
                    if profile:
                        # Update existing profile
                        conn.execute(
                            update(self.profile).where(self.profile.c.user_id == user_id).values(
                                age=age,
                                resting_hr=resting_hr,
                                weight=weight,
                                gender=gender
                            )
                        )
                    else:
                        # Create new profile
                        conn.execute(
                            insert(self.profile).values(
                                user_id=user_id,
                                age=age,
                                resting_hr=resting_hr,
                                weight=weight,
                                gender=gender
                            )
                        )
                    conn.commit()
                    print(f"Profile saved via SQLAlchemy for user {user_id}")
                    return True
            else:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    # Check if profile exists
                    cursor.execute('SELECT id FROM profile WHERE user_id = ?', (user_id,))
                    profile = cursor.fetchone()
                    
                    if profile:
                        # Update existing profile
                        cursor.execute('''
                            UPDATE profile 
                            SET age = ?, resting_hr = ?, weight = ?, gender = ? 
                            WHERE user_id = ?
                        ''', (age, resting_hr, weight, gender, user_id))
                    else:
                        # Create new profile
                        cursor.execute('''
                            INSERT INTO profile (user_id, age, resting_hr, weight, gender)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (user_id, age, resting_hr, weight, gender))
                        
                    conn.commit()
                    print(f"Profile saved via SQLite for user {user_id}")
                    return True
        except Exception as e:
            print(f"Error saving profile: {str(e)}")
            traceback.print_exc()
            return False 