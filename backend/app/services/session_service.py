"""Session tracking service for JWT lifecycle events."""

from datetime import datetime

from flask_jwt_extended import decode_token

from app import db
from app.models.session import Session


def _detect_device_type(user_agent):
    ua = (user_agent or '').lower()
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'mobile'
    if 'windows' in ua or 'macintosh' in ua or 'linux' in ua:
        return 'desktop'
    if ua:
        return 'web'
    return 'unknown'


def track_session(user_id, jwt_token, ip_address=None, user_agent=None):
    """Persist session metadata for an issued JWT token."""
    token_data = decode_token(jwt_token)
    jti = token_data.get('jti')
    exp = token_data.get('exp')
    if not jti:
        return None

    expires_at = datetime.utcfromtimestamp(exp) if exp else None
    existing = Session.query.filter_by(token_jti=jti).first()
    if existing:
        existing.last_activity = datetime.utcnow()
        existing.is_active = True
        return existing

    session = Session(
        user_id=user_id,
        token_jti=jti,
        ip_address=ip_address,
        user_agent=(user_agent or '')[:512] if user_agent else None,
        device_type=_detect_device_type(user_agent),
        expires_at=expires_at,
        is_active=True,
    )
    db.session.add(session)
    return session


def revoke_session(token_jti):
    """Deactivate one session by token JTI."""
    session = Session.query.filter_by(token_jti=token_jti).first()
    if session:
        session.is_active = False
        session.last_activity = datetime.utcnow()
    return session


def touch_session(token_jti):
    """Update last activity for an active session."""
    session = Session.query.filter_by(token_jti=token_jti, is_active=True).first()
    if session:
        session.last_activity = datetime.utcnow()
    return session
