"""
Flask Application Factory

Creates and configures the Flask application with all extensions,
blueprints, and error handlers.
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from app.config import config
from app.utils.i18n import get_localized_message

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

    # Development visibility: make missing SMTP obvious early.
    if config_name != 'testing':
        smtp_host = app.config.get('SMTP_HOST')
        smtp_from = app.config.get('SMTP_FROM')
        if not smtp_host or not smtp_from:
            app.logger.warning(
                "SMTP not fully configured. Verification/reset emails will not be delivered. "
                "Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM in backend/.env."
            )
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        from datetime import datetime
        from app.models.session import Session
        jti = jwt_payload.get('jti')
        if not jti:
            return False
        session = Session.query.filter_by(token_jti=jti).first()
        if not session:
            return False
        if not session.is_active:
            return True
        if session.expires_at and session.expires_at < datetime.utcnow():
            return True
        return False
    
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
    from app.routes import auth, posts, social, reactions, analytics, comments, notifications, bookmarks, zones
    
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(posts.bp, url_prefix='/api/posts')
    app.register_blueprint(social.bp, url_prefix='/api')
    app.register_blueprint(reactions.bp, url_prefix='/api/posts')
    app.register_blueprint(analytics.bp, url_prefix='/api/analytics')
    app.register_blueprint(comments.bp, url_prefix='/api')
    app.register_blueprint(notifications.bp, url_prefix='/api')
    app.register_blueprint(bookmarks.bp, url_prefix='/api')
    app.register_blueprint(zones.bp, url_prefix='/api')


def register_error_handlers(app):
    """
    Register global error handlers
    """
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': get_localized_message(request, 'not_found'),
            'message': get_localized_message(request, 'not_found')
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # Rollback any failed database transactions
        return jsonify({
            'error': get_localized_message(request, 'server_error'),
            'message': get_localized_message(request, 'server_error')
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': get_localized_message(request, 'validation_error')
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': get_localized_message(request, 'unauthorized'),
            'message': get_localized_message(request, 'unauthorized')
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': get_localized_message(request, 'forbidden'),
            'message': get_localized_message(request, 'forbidden')
        }), 403
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': get_localized_message(request, 'rate_limit_exceeded'),
            'message': get_localized_message(request, 'rate_limit_exceeded')
        }), 429
