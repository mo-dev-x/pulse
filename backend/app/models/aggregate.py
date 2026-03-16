"""
Aggregate Models - Privacy-Safe Analytics

Daily and weekly mood aggregation tables for campus wellness insights.
Aggregates are only shown when total_posts >= 10 (privacy threshold).
"""

from datetime import datetime, timezone
from app import db

DEFAULT_EMOTION_KEYS = ('joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise', 'neutral')
EMOTION_DISPLAY_MAP = {
    'joy': 'Joy',
    'sadness': 'Sad',
    'anger': 'Frustrated',
    'fear': 'Stressed',
    'disgust': 'Overwhelmed',
    'surprise': 'Surprised',
    'neutral': 'Neutral',
}


class DailyAggregate(db.Model):
    """
    Daily mood statistics per zone (or campus-wide if zone_id is NULL).

    Privacy Note:
    - Only shown when total_posts >= 10
    - No individual user data exposed
    - Aggregation prevents identification
    """

    __tablename__ = 'daily_aggregates'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Date and zone
    date = db.Column(db.Date, nullable=False)
    zone_id = db.Column(
        db.Integer,
        db.ForeignKey('campus_zones.id', ondelete='CASCADE'),
        nullable=True  # NULL = campus-wide
    )

    # Counts
    total_posts = db.Column(db.Integer, nullable=False, default=0)
    positive_count = db.Column(db.Integer, nullable=False, default=0)
    neutral_count = db.Column(db.Integer, nullable=False, default=0)
    negative_count = db.Column(db.Integer, nullable=False, default=0)

    # Statistics
    avg_sentiment = db.Column(db.Float, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    # Relationships
    zone = db.relationship('CampusZone', backref=db.backref('daily_aggregates', lazy='dynamic'))

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('date', 'zone_id', name='unique_daily_zone'),
    )

    # Privacy threshold
    MINIMUM_POSTS = 10

    def __repr__(self):
        zone_name = f'Zone {self.zone_id}' if self.zone_id else 'Campus-wide'
        return f'<DailyAggregate {self.date} {zone_name}: {self.total_posts} posts>'

    def to_dict(self, enforce_threshold=True):
        """
        Serialize to dictionary.

        Args:
            enforce_threshold: If True, returns None when total_posts < MINIMUM_POSTS
        """
        if enforce_threshold and self.total_posts < self.MINIMUM_POSTS:
            return {
                'date': self.date.isoformat(),
                'zone_id': self.zone_id,
                'message': 'Insufficient data for privacy-safe aggregation',
                'minimum_required': self.MINIMUM_POSTS,
                'current_count': self.total_posts
            }

        return {
            'date': self.date.isoformat(),
            'zone_id': self.zone_id,
            'total_posts': self.total_posts,
            'sentiment_distribution': {
                'positive': self.positive_count,
                'neutral': self.neutral_count,
                'negative': self.negative_count
            },
            'sentiment_percentages': {
                'positive': round(self.positive_count / self.total_posts * 100, 1) if self.total_posts > 0 else 0,
                'neutral': round(self.neutral_count / self.total_posts * 100, 1) if self.total_posts > 0 else 0,
                'negative': round(self.negative_count / self.total_posts * 100, 1) if self.total_posts > 0 else 0
            },
            'emotion_distribution': self._emotion_distribution(),
            'emotion_percentages': self._emotion_percentages(),
            'emotion_display_distribution': self._emotion_display_distribution(),
            'avg_sentiment': round(self.avg_sentiment, 2) if self.avg_sentiment is not None else None,
            'mood_label': self._get_mood_label()
        }

    def _get_mood_label(self):
        """Determine overall mood label from avg_sentiment"""
        if self.avg_sentiment is None:
            return 'unknown'
        if self.avg_sentiment > 0.05:
            return 'positive'
        elif self.avg_sentiment < -0.05:
            return 'negative'
        return 'neutral'

    def _emotion_distribution(self):
        distribution = getattr(self, 'emotion_distribution', None) or {}
        return {key: int(distribution.get(key, 0)) for key in DEFAULT_EMOTION_KEYS}

    def _emotion_percentages(self):
        distribution = self._emotion_distribution()
        if self.total_posts <= 0:
            return {key: 0 for key in DEFAULT_EMOTION_KEYS}
        return {
            key: round(distribution[key] / self.total_posts * 100, 1)
            for key in DEFAULT_EMOTION_KEYS
        }

    def _emotion_display_distribution(self):
        distribution = self._emotion_distribution()
        return {
            EMOTION_DISPLAY_MAP[key]: distribution[key]
            for key in DEFAULT_EMOTION_KEYS
        }


class WeeklyAggregate(db.Model):
    """
    Weekly mood statistics per zone (or campus-wide if zone_id is NULL).
    """

    __tablename__ = 'weekly_aggregates'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Week range and zone
    week_start = db.Column(db.Date, nullable=False)
    week_end = db.Column(db.Date, nullable=False)
    zone_id = db.Column(
        db.Integer,
        db.ForeignKey('campus_zones.id', ondelete='CASCADE'),
        nullable=True  # NULL = campus-wide
    )

    # Counts
    total_posts = db.Column(db.Integer, nullable=False, default=0)
    positive_count = db.Column(db.Integer, nullable=False, default=0)
    neutral_count = db.Column(db.Integer, nullable=False, default=0)
    negative_count = db.Column(db.Integer, nullable=False, default=0)

    # Statistics
    avg_sentiment = db.Column(db.Float, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    # Relationships
    zone = db.relationship('CampusZone', backref=db.backref('weekly_aggregates', lazy='dynamic'))

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('week_start', 'zone_id', name='unique_weekly_zone'),
    )

    # Privacy threshold
    MINIMUM_POSTS = 10

    def __repr__(self):
        zone_name = f'Zone {self.zone_id}' if self.zone_id else 'Campus-wide'
        return f'<WeeklyAggregate {self.week_start} - {self.week_end} {zone_name}>'

    def to_dict(self, enforce_threshold=True):
        """Serialize to dictionary with privacy threshold enforcement"""
        if enforce_threshold and self.total_posts < self.MINIMUM_POSTS:
            return {
                'week_start': self.week_start.isoformat(),
                'week_end': self.week_end.isoformat(),
                'zone_id': self.zone_id,
                'message': 'Insufficient data for privacy-safe aggregation',
                'minimum_required': self.MINIMUM_POSTS,
                'current_count': self.total_posts
            }

        return {
            'week_start': self.week_start.isoformat(),
            'week_end': self.week_end.isoformat(),
            'zone_id': self.zone_id,
            'total_posts': self.total_posts,
            'sentiment_distribution': {
                'positive': self.positive_count,
                'neutral': self.neutral_count,
                'negative': self.negative_count
            },
            'sentiment_percentages': {
                'positive': round(self.positive_count / self.total_posts * 100, 1) if self.total_posts > 0 else 0,
                'neutral': round(self.neutral_count / self.total_posts * 100, 1) if self.total_posts > 0 else 0,
                'negative': round(self.negative_count / self.total_posts * 100, 1) if self.total_posts > 0 else 0
            },
            'emotion_distribution': self._emotion_distribution(),
            'emotion_percentages': self._emotion_percentages(),
            'emotion_display_distribution': self._emotion_display_distribution(),
            'avg_sentiment': round(self.avg_sentiment, 2) if self.avg_sentiment is not None else None,
            'mood_label': self._get_mood_label()
        }

    def _get_mood_label(self):
        """Determine overall mood label from avg_sentiment"""
        if self.avg_sentiment is None:
            return 'unknown'
        if self.avg_sentiment > 0.05:
            return 'positive'
        elif self.avg_sentiment < -0.05:
            return 'negative'
        return 'neutral'

    def _emotion_distribution(self):
        distribution = getattr(self, 'emotion_distribution', None) or {}
        return {key: int(distribution.get(key, 0)) for key in DEFAULT_EMOTION_KEYS}

    def _emotion_percentages(self):
        distribution = self._emotion_distribution()
        if self.total_posts <= 0:
            return {key: 0 for key in DEFAULT_EMOTION_KEYS}
        return {
            key: round(distribution[key] / self.total_posts * 100, 1)
            for key in DEFAULT_EMOTION_KEYS
        }

    def _emotion_display_distribution(self):
        distribution = self._emotion_distribution()
        return {
            EMOTION_DISPLAY_MAP[key]: distribution[key]
            for key in DEFAULT_EMOTION_KEYS
        }
