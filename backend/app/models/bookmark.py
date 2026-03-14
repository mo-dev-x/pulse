"""Bookmark model for private saved posts."""

from datetime import datetime

from app import db


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_bookmark'),
    )

    user = db.relationship('User', backref=db.backref('bookmarks', lazy='dynamic', cascade='all, delete-orphan'))
    post = db.relationship('Post', backref=db.backref('bookmarks', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self, current_user_id=None):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'post': self.post.to_dict(current_user_id=current_user_id) if self.post else None,
        }
