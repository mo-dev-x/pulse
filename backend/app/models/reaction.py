"""
Reaction Model - Emoji Reactions on Posts

Users can react to posts (public or anonymous) with a single emoji.
Only one reaction per user per post. Only aggregate counts are exposed (privacy).
"""

from datetime import datetime
from app import db


class Reaction(db.Model):
    """
    Emoji reaction on a post.

    Privacy Notes:
    - API never exposes "who reacted" — only aggregate counts
    - One reaction per user per post (UNIQUE constraint)
    - Reactions on anonymous posts are allowed (AD-003)
    """

    __tablename__ = 'reactions'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # References
    post_id = db.Column(
        db.Integer,
        db.ForeignKey('posts.id', ondelete='CASCADE'),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    # Emoji (Unicode emoji character)
    emoji = db.Column(db.String(10), nullable=False)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    post = db.relationship('Post', backref=db.backref('reactions', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('reactions', lazy='dynamic'))

    # Table constraints
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_reaction'),
    )

    # Allowed emojis (subset for consistency)
    ALLOWED_EMOJIS = {'❤️', '👍', '👎', '😊', '😢', '😂', '😮', '🔥', '💪', '🙏'}

    def __repr__(self):
        return f'<Reaction {self.user_id} -> Post {self.post_id}: {self.emoji}>'

    @staticmethod
    def get_counts(post_id):
        """
        Get aggregate reaction counts for a post.
        Returns dict like: {"❤️": 12, "👍": 8}
        """
        # Use COUNT(*) and disable query caching for fresh results
        results = db.session.query(
            Reaction.emoji,
            db.func.count('*')
        ).filter(
            Reaction.post_id == post_id
        ).group_by(Reaction.emoji).execution_options(
            compiled_cache=None
        ).all()

        return {emoji: count for emoji, count in results}

    @staticmethod
    def get_user_reaction(user_id, post_id):
        """Get the current user's reaction on a post (if any)"""
        reaction = Reaction.query.filter_by(
            user_id=user_id,
            post_id=post_id
        ).first()
        return reaction.emoji if reaction else None

    @staticmethod
    def get_total_count(post_id):
        """Get total number of reactions on a post"""
        return Reaction.query.filter_by(post_id=post_id).count()
