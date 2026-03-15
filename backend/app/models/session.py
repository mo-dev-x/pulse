"""Session model for JWT session tracking and revocation."""

from datetime import datetime, timezone

from app import db


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_jti = db.Column(db.String(255), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    device_type = db.Column(
        db.Enum('web', 'mobile', 'desktop', 'unknown', name='session_device_type_enum'),
        nullable=False,
        default='unknown'
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('sessions', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'token_jti': self.token_jti,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_type': self.device_type,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'last_activity': self.last_activity.isoformat() + 'Z' if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() + 'Z' if self.expires_at else None,
            'is_active': self.is_active,
        }
