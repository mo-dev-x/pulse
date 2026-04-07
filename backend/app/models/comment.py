"""Comment model with one-level threading support."""

from datetime import datetime, timezone

from app import db


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'), nullable=True, index=True)
    is_anonymous = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    post = db.relationship('Post', backref=db.backref('comments', cascade='all, delete-orphan', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('comments', cascade='all, delete-orphan', lazy='dynamic'))
    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def to_dict(self, current_user_id=None):
        """Serialize comment with privacy-aware author payload."""
        data = {
            'id': self.id,
            'content': self.content,
            'post_id': self.post_id,
            'parent_id': self.parent_id,
            'is_anonymous': self.is_anonymous,
            'created_at': self.created_at.isoformat() + 'Z',
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None,
            'reply_count': self.replies.count()
        }

        if self.is_anonymous:
            data['author'] = {
                'pseudonym': self.user.pseudonym,
                'is_you': current_user_id == self.user_id if current_user_id else False
            }
        else:
            data['author'] = {
                'id': self.user.id,
                'username': self.user.username,
                'display_name': self.user.display_name,
                'profile_picture': self.user.profile_picture,
                'is_admin': self.user.is_admin
            }

        return data

    @staticmethod
    def validate_content(content):
        if not content:
            return False
        length = len(content.strip())
        return 1 <= length <= 500
