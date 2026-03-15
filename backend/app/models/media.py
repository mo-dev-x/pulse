"""
Media Model - Uploaded Images/Files for Posts

Supports image uploads attached to posts.
"""

from datetime import datetime, timezone
from app import db


class Media(db.Model):
    """
    Media attachment for a post.

    Supports image files (PNG, JPG, GIF, WebP).
    File type and size are validated before storage.
    """

    __tablename__ = 'media'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Reference to post
    post_id = db.Column(
        db.Integer,
        db.ForeignKey('posts.id', ondelete='CASCADE'),
        nullable=False
    )

    # File information
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(
        db.Enum('image', 'audio', 'video', name='file_type_enum'),
        nullable=False
    )
    file_size = db.Column(db.Integer, nullable=False)  # bytes
    mime_type = db.Column(db.String(100), nullable=True)

    # Timestamp
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relationships
    post = db.relationship('Post', backref=db.backref('media', lazy=True))

    def __repr__(self):
        return f'<Media {self.id}: {self.file_type} for Post {self.post_id}>'

    def to_dict(self):
        """Serialize media to dictionary"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat() + 'Z' if self.uploaded_at else None
        }
