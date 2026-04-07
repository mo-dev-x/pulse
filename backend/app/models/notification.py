"""Notification model for user activity updates."""

from datetime import datetime, timezone

from app import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = db.Column(
        db.Enum(
            'new_follower',
            'new_comment',
            'comment_reply',
            'post_reaction',
            'mention',
            'system',
            name='notification_type_enum'
        ),
        nullable=False,
        index=True
    )
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    related_type = db.Column(
        db.Enum('post', 'comment', 'user', name='notification_related_type_enum'),
        nullable=True
    )
    related_id = db.Column(db.Integer, nullable=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False, index=True)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy='dynamic'))
    actor = db.relationship('User', foreign_keys=[actor_id])

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'actor': {
                'id': self.actor.id,
                'username': self.actor.username,
                'display_name': self.actor.display_name,
                'profile_picture': self.actor.profile_picture,
                'is_admin': self.actor.is_admin,
            } if self.actor else None,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }
