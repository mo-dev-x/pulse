"""
Models package

Imports all SQLAlchemy models for easy access.
Models are imported here to avoid circular imports.
"""

from app.models.user import User
from app.models.post import Post
from app.models.campus_zone import CampusZone
from app.models.follower import Follower
from app.models.reaction import Reaction
from app.models.media import Media
from app.models.aggregate import DailyAggregate, WeeklyAggregate

__all__ = [
    'User', 'Post', 'CampusZone',
    'Follower', 'Reaction', 'Media',
    'DailyAggregate', 'WeeklyAggregate'
]