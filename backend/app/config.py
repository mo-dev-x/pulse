"""
Flask Configuration

Defines configuration classes for different environments (development, production).
Loads sensitive values from environment variables.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Base configuration class with common settings
    """
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400)))
    JWT_ALGORITHM = 'HS256'
    
    # Database Configuration
    DB_HOST = os.getenv('MYSQLHOST', 'localhost')
    DB_PORT = int(os.getenv('MYSQLPORT', 3306))
    DB_NAME = os.getenv('MYSQLDATABASE', 'pulse_db')
    DB_USER = os.getenv('MYSQLUSER', 'root')
    DB_PASSWORD = os.getenv('MYSQLPASSWORD', '')
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries in console
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,   # drop and replace stale connections silently
        'pool_recycle': 280,     # recycle before MySQL's 300 s wait_timeout
    }
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5242880))  # 5MB default
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
    PROFILE_UPLOAD_FOLDER = os.getenv('PROFILE_UPLOAD_FOLDER', 'uploads/profiles')
    HEADER_UPLOAD_FOLDER = os.getenv('HEADER_UPLOAD_FOLDER', 'uploads/headers')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_MIME_TYPES = {
        'image/png',
        'image/jpeg', 
        'image/gif',
        'image/webp'
    }
    
    # CORS Configuration
    CORS_HEADERS = 'Content-Type'

    # Frontend integration
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    _default_cors_origins = [
        'http://127.0.0.1:8000',
        'http://localhost:8000',
        'http://127.0.0.1:5500',
        'http://localhost:5500',
        'http://127.0.0.1:5501',
        'http://localhost:5501',
        'http://127.0.0.1:5173',
        'http://localhost:5173',
        'http://127.0.0.1:4173',
        'http://localhost:4173',
        'http://127.0.0.1:5000',
        'http://localhost:5000',
        'https://pulse-seven-blond.vercel.app',
    ]
    _default_cors_origin_patterns = [
        r'https://.*',
        r'http://localhost(?::\d+)?',
        r'http://127\.0\.0\.1(?::\d+)?',
    ]
    _configured_cors_origins = [
        origin.strip()
        for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
        if origin.strip()
    ]
    _configured_cors_origin_patterns = [
        origin.strip()
        for origin in os.getenv('CORS_ALLOWED_ORIGIN_PATTERNS', '').split(',')
        if origin.strip()
    ]
    if FRONTEND_URL:
        _configured_cors_origins.append(FRONTEND_URL)
    CORS_ALLOWED_ORIGINS = list(dict.fromkeys(_default_cors_origins + _configured_cors_origins))
    CORS_ALLOWED_ORIGIN_PATTERNS = list(
        dict.fromkeys(_default_cors_origin_patterns + _configured_cors_origin_patterns)
    )

    # Brevo email configuration
    BREVO_API_KEY = os.getenv('BREVO_API_KEY')
    BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL')

    # OIDC / Azure Entra configuration
    ENABLE_OIDC_AUTH = os.getenv('ENABLE_OIDC_AUTH', 'false').lower() == 'true'
    OIDC_AUTHORIZE_URL = os.getenv('OIDC_AUTHORIZE_URL')
    OIDC_TOKEN_URL = os.getenv('OIDC_TOKEN_URL')
    OIDC_USERINFO_URL = os.getenv('OIDC_USERINFO_URL')
    OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID')
    OIDC_CLIENT_SECRET = os.getenv('OIDC_CLIENT_SECRET')
    OIDC_REDIRECT_URI = os.getenv('OIDC_REDIRECT_URI', 'http://127.0.0.1:5000/api/auth/oidc/callback')
    OIDC_SCOPE = os.getenv('OIDC_SCOPE', 'openid profile email')
    ENABLE_MEILISEARCH = os.getenv('ENABLE_MEILISEARCH', 'false').lower() == 'true'
    MEILISEARCH_URL = os.getenv('MEILISEARCH_URL', 'http://127.0.0.1:7700')
    MEILISEARCH_API_KEY = os.getenv('MEILISEARCH_API_KEY')
    MEILISEARCH_POSTS_INDEX = os.getenv('MEILISEARCH_POSTS_INDEX', 'posts')
    MEILISEARCH_USERS_INDEX = os.getenv('MEILISEARCH_USERS_INDEX', 'users')
    MEILISEARCH_ZONES_INDEX = os.getenv('MEILISEARCH_ZONES_INDEX', 'zones')
    REDIS_URL = os.getenv('REDIS_URL')
    BACKGROUND_JOBS_ENABLED = os.getenv('BACKGROUND_JOBS_ENABLED', 'false').lower() == 'true'
    BACKGROUND_JOBS_EAGER = os.getenv('BACKGROUND_JOBS_EAGER', 'false').lower() == 'true'
    BACKGROUND_JOB_TIMEOUT = int(os.getenv('BACKGROUND_JOB_TIMEOUT', 300))
    PUSH_ENABLED = os.getenv('PUSH_ENABLED', 'false').lower() == 'true'
    FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY')


class DevelopmentConfig(Config):
    """
    Development environment configuration
    """
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Show SQL queries in development


class ProductionConfig(Config):
    """
    Production environment configuration
    """
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """
    Testing environment configuration
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for tests
    WTF_CSRF_ENABLED = False
    BACKGROUND_JOBS_ENABLED = False
    BACKGROUND_JOBS_EAGER = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
