"""
Flask Application Factory

Creates and configures the Flask application with all extensions,
blueprints, and error handlers.
"""

from datetime import datetime, timezone
import os
import re
from flask import Flask, app, jsonify, request, send_from_directory
from sqlalchemy import text
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import config
from app.utils.i18n import get_localized_message

# Initialize extensions (without binding to app yet)
db = SQLAlchemy()
jwt = JWTManager()
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri='memory://',
)


def rate_limit_key_user():
    """Prefer authenticated user id for limits, fallback to remote IP."""
    identity = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
    if identity:
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
            verify_jwt_in_request(optional=True)
            jwt_identity = get_jwt_identity()
            if jwt_identity:
                return f"user:{jwt_identity}"
        except Exception:
            pass
    return get_remote_address()


def rate_limit_value(config_key, default):
    """Read a rate limit string from app config at request time."""
    def _resolver():
        from flask import current_app
        return current_app.config.get(config_key, default)
    return _resolver


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

    base_dir = os.path.abspath(os.path.join(app.root_path, '..'))
    upload_root = os.path.join(base_dir, 'uploads')

    app.config['UPLOAD_FOLDER'] = upload_root
    app.config['PROFILE_UPLOAD_FOLDER'] = os.path.join(upload_root, 'profiles')
    app.config['HEADER_UPLOAD_FOLDER'] = os.path.join(upload_root, 'headers')

    # Development visibility: make missing API keys obvious early.
    if config_name != 'testing':
        brevo_key = app.config.get('BREVO_API_KEY')
        if not brevo_key:
            app.logger.warning(
                "Brevo API key not configured. Verification/reset emails will not be delivered. "
                "Set BREVO_API_KEY and BREVO_SENDER_EMAIL in Railway environment variables."
            )
        hf_key = app.config.get('HUGGINGFACE_API_KEY')
        if not hf_key:
            app.logger.warning(
                "HUGGINGFACE_API_KEY not configured. French sentiment analysis will fall back to VADER. "
                "Set HUGGINGFACE_API_KEY in Railway environment variables."
            )
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    cors_origins = app.config.get('CORS_ALLOWED_ORIGINS', []) + app.config.get('CORS_ALLOWED_ORIGIN_PATTERNS', [])
    CORS(
        app,
        resources={
            r"/api/*": {"origins": cors_origins},
            r"/uploads/*": {"origins": cors_origins},
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "Accept-Language"],
        expose_headers=["Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        vary_header=True,
        max_age=86400,
    )
    limiter.init_app(app)

    allowed_exact_origins = app.config.get('CORS_ALLOWED_ORIGINS', [])
    allowed_origin_patterns = [
        re.compile(pattern)
        for pattern in app.config.get('CORS_ALLOWED_ORIGIN_PATTERNS', [])
    ]

    def _cors_origin_for_request():
        origin = request.headers.get('Origin')
        if not origin:
            return None
        if origin in allowed_exact_origins:
            return origin
        for pattern in allowed_origin_patterns:
            if pattern.fullmatch(origin):
                return origin
        return None

    @app.before_request
    def handle_cors_preflight():
        if request.method != 'OPTIONS':
            return None
        if not (request.path.startswith('/api/') or request.path.startswith('/uploads/')):
            return None

        origin = _cors_origin_for_request()
        if not origin:
            return None

        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept-Language'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '86400'
        response.headers.add('Vary', 'Origin')
        return response

    @app.after_request
    def add_cors_headers(response):
        if not (request.path.startswith('/api/') or request.path.startswith('/uploads/')):
            return response

        origin = _cors_origin_for_request()
        if not origin:
            return response

        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept-Language'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '86400'
        response.headers.add('Vary', 'Origin')
        return response

    # AUTO CREATE DATABASE TABLES ON START (Railway)
    if config_name == "production":
        with app.app_context():
            from setup_db import setup_database
            setup_database()

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        from app.models.session import Session
        jti = jwt_payload.get('jti')
        if not jti:
            return False
        # Cache valid JTIs for 30 s to avoid a DB round-trip on every request.
        # Revoked sessions stay effective within 30 s of logout (acceptable).
        cache_key = f'jti_valid:{jti}'
        cached = cache.get(cache_key)
        if cached is True:
            return False  # known-valid, skip DB
        session = Session.query.filter_by(token_jti=jti).first()
        if not session:
            return False
        if not session.is_active:
            return True
        if session.expires_at and session.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            return True
        cache.set(cache_key, True, timeout=30)
        return False
    
    # Register blueprints
    register_blueprints(app)

    # ── Lightweight schema migrations (idempotent, run on every boot) ──────────
    # Adds columns that were introduced after the initial schema.sql was run.
    # Each ALTER TABLE is wrapped in try/except so it silently skips when the
    # column already exists (MySQL raises 1060 on duplicate column).
    _migrate_schema(app)

    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Eagerly import the user model in development so SQLAlchemy is aware of it
    # without relying solely on blueprint imports. Schema is managed via SQL scripts.
    if config_name == 'development':
        with app.app_context():
            from app.models import user  # noqa: F401
            from app.models import mood_checkin  # noqa: F401
            db.create_all()

    if config_name == 'production':
        with app.app_context():
            from app.models import mood_checkin  # noqa: F401
            db.create_all()
    
    return app


def _migrate_schema(app):
    """Add columns introduced after the initial schema without dropping data."""
    migrations = [
        "ALTER TABLE messages ADD COLUMN reply_to_id INT NULL",
        "ALTER TABLE messages ADD COLUMN reply_preview VARCHAR(255) NULL",
        "ALTER TABLE messages ADD INDEX ix_messages_reply_to_id (reply_to_id)",
        # Cloudinary: store CDN URL alongside the legacy local file_path
        "ALTER TABLE media ADD COLUMN media_url VARCHAR(500) NULL",
    ]
    with app.app_context():
        with db.engine.connect() as conn:
            for sql in migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception:
                    # Column / index already exists — safe to ignore
                    pass


def register_blueprints(app):
    """
    Register all Flask blueprints
    """
    from app.routes import auth, posts, social, reactions, analytics, comments, notifications, bookmarks, zones, search, reports, messages, push, mood, uploads

    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(uploads.bp, url_prefix='/api')
    app.register_blueprint(posts.bp, url_prefix='/api/posts')
    app.register_blueprint(social.bp, url_prefix='/api')
    app.register_blueprint(reactions.bp, url_prefix='/api/posts')
    app.register_blueprint(analytics.bp, url_prefix='/api/analytics')
    app.register_blueprint(comments.bp, url_prefix='/api')
    app.register_blueprint(notifications.bp, url_prefix='/api')
    app.register_blueprint(bookmarks.bp, url_prefix='/api')
    app.register_blueprint(zones.bp, url_prefix='/api')
    app.register_blueprint(search.bp, url_prefix='/api')
    app.register_blueprint(reports.bp, url_prefix='/api')
    app.register_blueprint(messages.bp, url_prefix='/api')
    app.register_blueprint(push.bp, url_prefix='/api')
    app.register_blueprint(mood.bp, url_prefix='/api')


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
        retry_after = getattr(error, 'retry_after', None)
        if retry_after is None:
            retry_after = getattr(getattr(error, 'description', None), 'retry_after', None)
        if retry_after is not None:
            try:
                retry_after = int(retry_after)
            except (TypeError, ValueError):
                retry_after = None

        return jsonify({
            'error': get_localized_message(request, 'rate_limit_exceeded'),
            'message': get_localized_message(request, 'rate_limit_exceeded'),
            'retry_after': retry_after
        }), 429
