"""
Flask Application Factory

Creates and configures the Flask application with all extensions,
blueprints, and error handlers.
"""

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from app.config import config

# Initialize extensions (without binding to app yet)
db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name='development'):
    """
    Application factory function
    
    Args:
        config_name (str): Configuration to use ('development', 'production', 'testing')
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables (in development only)
    if config_name == 'development':
        with app.app_context():
            # Import models here to avoid circular imports
            # NOTE: Only import models that exist!
            from app.models import user
            # We'll uncomment these as we create them:
            # from app.models import post, campus_zone, media, reaction, aggregate
            # db.create_all()  # Commented out - we'll use SQL script instead
    
    return app


def register_blueprints(app):
    """
    Register all Flask blueprints
    """
    from app.routes import auth, posts, social, reactions, analytics
    
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(posts.bp, url_prefix='/api/posts')
    app.register_blueprint(social.bp, url_prefix='/api')
    app.register_blueprint(reactions.bp, url_prefix='/api/posts')
    app.register_blueprint(analytics.bp, url_prefix='/api/analytics')


def register_error_handlers(app):
    """
    Register global error handlers
    """
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource does not exist'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # Rollback any failed database transactions
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': 'Invalid request data'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429