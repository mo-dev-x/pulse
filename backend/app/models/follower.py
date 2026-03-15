"""
Follower Model - Social Graph

Represents one-way follow relationships between users.
Friends are computed as mutual follows (not stored separately).
"""

from datetime import datetime, timezone
from app import db


class Follower(db.Model):
    """
    One-way follow relationship.

    Privacy Note:
    - Following is public (users can see who follows whom)
    - Friends = mutual follows (computed, not stored)
    - Followers can NOT see friends' anonymous posts
    """

    __tablename__ = 'followers'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # The user who clicks "follow"
    follower_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    # The user being followed
    following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    # Timestamp
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relationships
    follower = db.relationship(
        'User',
        foreign_keys=[follower_id],
        backref=db.backref('following_records', lazy='dynamic')
    )
    following = db.relationship(
        'User',
        foreign_keys=[following_id],
        backref=db.backref('follower_records', lazy='dynamic')
    )

    # Table constraints
    __table_args__ = (
        db.UniqueConstraint('follower_id', 'following_id', name='unique_follow'),
    )

    def __repr__(self):
        return f'<Follower {self.follower_id} -> {self.following_id}>'

    @staticmethod
    def is_following(follower_id, following_id):
        """Check if user A follows user B"""
        return Follower.query.filter_by(
            follower_id=follower_id,
            following_id=following_id
        ).first() is not None

    @staticmethod
    def get_followers(user_id):
        """Get list of users who follow the given user"""
        return Follower.query.filter_by(following_id=user_id).all()

    @staticmethod
    def get_following(user_id):
        """Get list of users the given user follows"""
        return Follower.query.filter_by(follower_id=user_id).all()

    @staticmethod
    def get_following_ids(user_id):
        """Get list of user IDs that user_id follows (for feed generation)"""
        results = db.session.query(Follower.following_id).filter(
            Follower.follower_id == user_id
        ).all()
        return [r[0] for r in results]

    @staticmethod
    def get_friends(user_id):
        """
        Get mutual follows (friends).

        Friends = users where:
        1. I follow them
        2. They follow me
        """
        from app.models.user import User

        # Subquery: IDs of people I follow
        i_follow = db.session.query(Follower.following_id).filter(
            Follower.follower_id == user_id
        ).subquery()

        # Subquery: IDs of people who follow me
        follow_me = db.session.query(Follower.follower_id).filter(
            Follower.following_id == user_id
        ).subquery()

        # Intersection = friends
        friends = User.query.filter(
            User.id.in_(i_follow),
            User.id.in_(follow_me)
        ).all()

        return friends

    @staticmethod
    def get_follower_count(user_id):
        """Count how many people follow this user"""
        return Follower.query.filter_by(following_id=user_id).count()

    @staticmethod
    def get_following_count(user_id):
        """Count how many people this user follows"""
        return Follower.query.filter_by(follower_id=user_id).count()
