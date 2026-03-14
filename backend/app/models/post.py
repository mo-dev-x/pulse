"""
Post Model - Content with Sentiment Analysis
Supports both public and anonymous posting
"""

from datetime import datetime
from app import db

class Post(db.Model):
    __tablename__ = 'posts'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Content
    content = db.Column(db.Text, nullable=False)
    
    # Author (ALWAYS stored, even for anonymous posts)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Location (Optional)
    zone_id = db.Column(db.Integer, db.ForeignKey('campus_zones.id'), nullable=True)
    
    # Privacy
    is_anonymous = db.Column(db.Boolean, default=False, nullable=False)
    
    # Sentiment Analysis Results
    sentiment_score = db.Column(db.Float, nullable=True)  # -1.0 to 1.0
    sentiment_label = db.Column(
        db.Enum('positive', 'neutral', 'negative', name='sentiment_enum'),
        nullable=True
    )
    detected_language = db.Column(db.String(2), nullable=True)  # 'en' or 'fr'
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship(
        'User',
        foreign_keys=[user_id],
        backref=db.backref('posts', lazy=True, foreign_keys='Post.user_id')
    )
    zone = db.relationship('CampusZone', backref='posts', lazy=True)
    
    def __repr__(self):
        return f'<Post {self.id}: {"Anonymous" if self.is_anonymous else "Public"}>'
    
    def to_dict(self, current_user_id=None):
        """
        Serialize post to dictionary
        Privacy-aware: hides user_id for anonymous posts
        
        Args:
            current_user_id: ID of the requesting user (to show "is_you" flag)
        """
        data = {
            'id': self.id,
            'content': self.content,
            'is_anonymous': self.is_anonymous,
            'sentiment': self.sentiment_label,
            'sentiment_score': round(self.sentiment_score, 2) if self.sentiment_score else None,
            'detected_language': self.detected_language,
            'created_at': self.created_at.isoformat() + 'Z',
        }
        
        # Zone information
        if self.zone:
            data['zone'] = {
                'id': self.zone.id,
                'name': self.zone.name,
                'type': self.zone.zone_type
            }
        else:
            data['zone'] = None
        
        # Author information (privacy-aware)
        if self.is_anonymous:
            # Anonymous post: show pseudonym only
            data['author'] = {
                'pseudonym': self.author.pseudonym,
                'is_you': (current_user_id == self.user_id) if current_user_id else False
            }
        else:
            # Public post: show full profile
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username,
                'display_name': self.author.display_name,
                'profile_picture': self.author.profile_picture
            }
        
        return data
    
    def validate_content(self):
        """Validate post content length"""
        if not self.content or len(self.content.strip()) < 10:
            return False, "Content must be at least 10 characters"
        if len(self.content) > 500:
            return False, "Content must not exceed 500 characters"
        return True, None
