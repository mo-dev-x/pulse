"""Push notification subscription model."""

from datetime import datetime, timezone

from app import db


class PushSubscription(db.Model):
    __tablename__ = 'push_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    platform = db.Column(
        db.Enum('web', 'ios', 'android', name='push_platform_enum'),
        nullable=False,
        index=True
    )
    token = db.Column(db.Text, nullable=False)
    device_label = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'platform': self.platform,
            'token': self.token,
            'device_label': self.device_label,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() + 'Z' if self.last_used_at else None,
        }
