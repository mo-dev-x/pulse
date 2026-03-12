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
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'pulse_db')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries in console
    
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

    # SMTP configuration
    SMTP_HOST = os.getenv('SMTP_HOST')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_FROM = os.getenv('SMTP_FROM', 'noreply@pulse.ulaval.ca')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

    # OIDC / Azure Entra configuration
    ENABLE_OIDC_AUTH = os.getenv('ENABLE_OIDC_AUTH', 'false').lower() == 'true'
    OIDC_AUTHORIZE_URL = os.getenv('OIDC_AUTHORIZE_URL')
    OIDC_TOKEN_URL = os.getenv('OIDC_TOKEN_URL')
    OIDC_USERINFO_URL = os.getenv('OIDC_USERINFO_URL')
    OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID')
    OIDC_CLIENT_SECRET = os.getenv('OIDC_CLIENT_SECRET')
    OIDC_REDIRECT_URI = os.getenv('OIDC_REDIRECT_URI', 'http://127.0.0.1:5000/api/auth/oidc/callback')
    OIDC_SCOPE = os.getenv('OIDC_SCOPE', 'openid profile email')


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
    
    # In production, these MUST be set via environment variables
    @property
    def SECRET_KEY(self):
        secret = os.getenv('SECRET_KEY')
        if not secret or secret == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production environment")
        return secret
    
    @property
    def JWT_SECRET_KEY(self):
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if not jwt_secret or jwt_secret == 'dev-jwt-secret-change-in-production':
            raise ValueError("JWT_SECRET_KEY must be set in production environment")
        return jwt_secret


class TestingConfig(Config):
    """
    Testing environment configuration
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for tests
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
