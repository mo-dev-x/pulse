"""Security logging helper service."""

from app import db
from app.models.security_log import SecurityLog


def log_security_event(event_type, user_id=None, ip_address=None, user_agent=None, metadata=None):
    """Insert a security event into audit logs."""
    event = SecurityLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=(user_agent or '')[:512] if user_agent else None,
        metadata_json=metadata or None,
    )
    db.session.add(event)
    return event
