import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    SESSION_COOKIE_NAME = 'running_session'  # Custom session cookie name

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FRONTEND_URL = 'http://localhost:3000'
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///runs.db')

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://your-app-name.onrender.com')
    DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Ensure PostgreSQL works with SQLAlchemy
    @property
    def DATABASE_URI(self):
        uri = os.environ.get('DATABASE_URL')
        if uri and uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        return uri

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 