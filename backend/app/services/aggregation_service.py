"""
Aggregation Service

Computes daily and weekly mood statistics from posts.
Enforces privacy threshold (≥10 posts) before exposing data.
"""

from datetime import datetime, timedelta, date
from app import db
from app.models.post import Post
from app.models.aggregate import DailyAggregate, WeeklyAggregate
from app.models.campus_zone import CampusZone


def compute_daily_aggregate(target_date, zone_id=None):
    """
    Compute or update daily aggregate for a specific date and zone.

    Args:
        target_date (date): The date to aggregate
        zone_id (int, optional): Zone ID, or None for campus-wide

    Returns:
        DailyAggregate: The created/updated aggregate record
    """
    # Build base query for the target date
    query = Post.query.filter(
        db.func.date(Post.created_at) == target_date
    )

    if zone_id is not None:
        query = query.filter(Post.zone_id == zone_id)

    # Count by sentiment label
    posts = query.all()
    total = len(posts)
    positive = sum(1 for p in posts if p.sentiment_label == 'positive')
    neutral = sum(1 for p in posts if p.sentiment_label == 'neutral')
    negative = sum(1 for p in posts if p.sentiment_label == 'negative')

    # Compute average sentiment score
    scores = [p.sentiment_score for p in posts if p.sentiment_score is not None]
    avg_sentiment = sum(scores) / len(scores) if scores else None

    # Upsert aggregate record
    existing = DailyAggregate.query.filter_by(
        date=target_date,
        zone_id=zone_id
    ).first()

    if existing:
        existing.total_posts = total
        existing.positive_count = positive
        existing.neutral_count = neutral
        existing.negative_count = negative
        existing.avg_sentiment = avg_sentiment
        aggregate = existing
    else:
        aggregate = DailyAggregate(
            date=target_date,
            zone_id=zone_id,
            total_posts=total,
            positive_count=positive,
            neutral_count=neutral,
            negative_count=negative,
            avg_sentiment=avg_sentiment
        )
        db.session.add(aggregate)

    db.session.commit()
    return aggregate


def compute_weekly_aggregate(week_start_date, zone_id=None):
    """
    Compute or update weekly aggregate for a specific week and zone.

    Args:
        week_start_date (date): Monday of the week to aggregate
        zone_id (int, optional): Zone ID, or None for campus-wide

    Returns:
        WeeklyAggregate: The created/updated aggregate record
    """
    week_end_date = week_start_date + timedelta(days=6)

    # Build query for the week
    query = Post.query.filter(
        db.func.date(Post.created_at) >= week_start_date,
        db.func.date(Post.created_at) <= week_end_date
    )

    if zone_id is not None:
        query = query.filter(Post.zone_id == zone_id)

    # Count by sentiment label
    posts = query.all()
    total = len(posts)
    positive = sum(1 for p in posts if p.sentiment_label == 'positive')
    neutral = sum(1 for p in posts if p.sentiment_label == 'neutral')
    negative = sum(1 for p in posts if p.sentiment_label == 'negative')

    # Compute average sentiment score
    scores = [p.sentiment_score for p in posts if p.sentiment_score is not None]
    avg_sentiment = sum(scores) / len(scores) if scores else None

    # Upsert aggregate record
    existing = WeeklyAggregate.query.filter_by(
        week_start=week_start_date,
        zone_id=zone_id
    ).first()

    if existing:
        existing.total_posts = total
        existing.positive_count = positive
        existing.neutral_count = neutral
        existing.negative_count = negative
        existing.avg_sentiment = avg_sentiment
        existing.week_end = week_end_date
        aggregate = existing
    else:
        aggregate = WeeklyAggregate(
            week_start=week_start_date,
            week_end=week_end_date,
            zone_id=zone_id,
            total_posts=total,
            positive_count=positive,
            neutral_count=neutral,
            negative_count=negative,
            avg_sentiment=avg_sentiment
        )
        db.session.add(aggregate)

    db.session.commit()
    return aggregate


def compute_all_daily_aggregates(target_date):
    """
    Compute daily aggregates for a date across all zones + campus-wide.

    Args:
        target_date (date): Date to compute aggregates for

    Returns:
        list: List of DailyAggregate objects
    """
    aggregates = []

    # Campus-wide aggregate (zone_id=None)
    aggregates.append(compute_daily_aggregate(target_date, zone_id=None))

    # Per-zone aggregates
    zones = CampusZone.get_all_active()
    for zone in zones:
        aggregates.append(compute_daily_aggregate(target_date, zone_id=zone.id))

    return aggregates


def compute_all_weekly_aggregates(week_start_date):
    """
    Compute weekly aggregates for a week across all zones + campus-wide.

    Args:
        week_start_date (date): Monday of the week

    Returns:
        list: List of WeeklyAggregate objects
    """
    aggregates = []

    # Campus-wide aggregate
    aggregates.append(compute_weekly_aggregate(week_start_date, zone_id=None))

    # Per-zone aggregates
    zones = CampusZone.get_all_active()
    for zone in zones:
        aggregates.append(compute_weekly_aggregate(week_start_date, zone_id=zone.id))

    return aggregates


def get_campus_mood_overview(target_date):
    """
    Get a campus-wide mood overview for a specific date.

    Returned even if below threshold, but marked as insufficient data.

    Args:
        target_date (date): Date to get overview for

    Returns:
        dict: Campus mood overview
    """
    # Ensure daily aggregate is computed
    campus_agg = compute_daily_aggregate(target_date, zone_id=None)

    # Get per-zone data
    zones = CampusZone.get_all_active()
    zone_data = []
    for zone in zones:
        agg = compute_daily_aggregate(target_date, zone_id=zone.id)
        zone_dict = agg.to_dict(enforce_threshold=True)
        zone_dict['zone_name'] = zone.name
        zone_dict['zone_type'] = zone.zone_type
        zone_data.append(zone_dict)

    return {
        'date': target_date.isoformat(),
        'campus_wide': campus_agg.to_dict(enforce_threshold=True),
        'zones': zone_data,
        'disclaimer': 'Sentiment analysis is automated and approximate. '
                       'It shows campus trends, not individual diagnoses. '
                       'If you are struggling, contact Campus Counseling.'
    }
