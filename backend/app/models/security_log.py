"""Security audit log model."""

from datetime import datetime

from app import db


class SecurityLog(db.Model):
    __tablename__ = 'security_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    event_type = db.Column(
        db.Enum(
            'login_success',
            'login_failed',
            'logout',
            'password_change',
            'password_reset',
            '2fa_enabled',
            '2fa_disabled',
            '2fa_verify_failed',
            'account_deactivated',
            'account_reactivated',
            'session_revoked',
            name='security_event_type_enum'
        ),
        nullable=False,
        index=True
    )
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('security_logs', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'metadata': self.metadata_json,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }
