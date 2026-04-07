"""Direct message model."""

from datetime import datetime, timezone

from app import db


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False, index=True)

    conversation = db.relationship('Conversation', backref=db.backref('messages', cascade='all, delete-orphan', lazy='dynamic'))
    sender = db.relationship('User', backref=db.backref('messages_sent', lazy='dynamic'))

    def to_dict(self, current_user_id=None):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'content': self.content,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() + 'Z' if self.read_at else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'is_mine': current_user_id == self.sender_id if current_user_id else False,
        }

    @staticmethod
    def validate_content(content):
        if content is None:
            return False
        stripped = content.strip()
        # Media messages carry a special prefix — bypass length check
        if stripped.startswith(('[audio]', '[image]', '[video]')):
            return len(stripped) > 7
        length = len(stripped)
        return 1 <= length <= 1000
