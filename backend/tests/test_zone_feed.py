"""Automated tests for Phase 6 zone feed endpoints."""

from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models import CampusZone, Post, Reaction, User
from tests.phase5_test_utils import Phase5BaseTestCase


class TestZoneFeed(Phase5BaseTestCase):

    def setUp(self):
        super().setUp()
        self.viewer_token, _ = self.register_user(email='zone_viewer@ulaval.ca', username='zone_viewer')
        self.mark_verified('zone_viewer@ulaval.ca')

        self.zone = CampusZone(
            name='PEPS - Pavillon principal',
            description='Centre sportif principal',
            zone_type='sports',
        )
        db.session.add(self.zone)
        db.session.flush()

        self.author = User(email='zone_author@ulaval.ca', password='SecurePass123', username='zone_author', display_name='Zone Author', is_verified=True)
        self.reactor = User(email='zone_reactor@ulaval.ca', password='SecurePass123', username='zone_reactor', display_name='Zone Reactor', is_verified=True)
        db.session.add_all([self.author, self.reactor])
        db.session.flush()

        self.public_positive = self._make_post('Morning run at PEPS feels great today.', 'positive', 0.8, datetime.utcnow() - timedelta(hours=2))
        self.public_neutral = self._make_post('PEPS is busy this afternoon but manageable.', 'neutral', 0.0, datetime.utcnow() - timedelta(hours=1))
        self.public_negative = self._make_post('Locker room line is frustrating today at PEPS.', 'negative', -0.6, datetime.utcnow() - timedelta(hours=3))
        self._make_post('Anonymous PEPS post should not be listed.', 'neutral', 0.0, datetime.utcnow() - timedelta(minutes=30), is_anonymous=True)

        db.session.flush()
        db.session.add_all([
            Reaction(post_id=self.public_positive.id, user_id=self.reactor.id, emoji='❤️'),
            Reaction(post_id=self.public_positive.id, user_id=self.author.id, emoji='🔥'),
            Reaction(post_id=self.public_neutral.id, user_id=self.reactor.id, emoji='❤️'),
        ])
        db.session.commit()

    def _make_post(self, content, sentiment_label, sentiment_score, created_at, is_anonymous=False):
        post = Post(
            content=content,
            user_id=self.author.id,
            zone_id=self.zone.id,
            is_anonymous=is_anonymous,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            detected_language='en',
        )
        post.created_at = created_at
        db.session.add(post)
        return post

    def test_zone_feed_returns_paginated_posts(self):
        response = self.client.get(
            f'/api/posts/zone/{self.zone.id}?page=1&per_page=2',
            headers=self.auth_headers(self.viewer_token),
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertEqual(payload['page'], 1)
        self.assertEqual(payload['pages'], 2)
        self.assertEqual(len(payload['posts']), 2)
        self.assertTrue(payload['has_next'])

    def test_zone_feed_excludes_anonymous_posts(self):
        response = self.client.get(f'/api/posts/zone/{self.zone.id}', headers=self.auth_headers(self.viewer_token))
        self.assertEqual(response.status_code, 200, response.get_json())
        contents = [post['content'] for post in response.get_json()['posts']]
        self.assertNotIn('Anonymous PEPS post should not be listed.', contents)

    def test_zone_activity_summary_returns_correct_sentiment_breakdown(self):
        response = self.client.get(f'/api/zones/{self.zone.id}/activity')
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        last_24h = payload['last_24h']
        self.assertEqual(last_24h['post_count'], 3)
        self.assertEqual(last_24h['reaction_count'], 3)
        self.assertEqual(last_24h['dominant_sentiment'], 'positive')
        self.assertEqual(last_24h['sentiment_breakdown']['positive'], 0.33)
        self.assertEqual(last_24h['sentiment_breakdown']['neutral'], 0.33)
        self.assertEqual(last_24h['sentiment_breakdown']['negative'], 0.33)
        self.assertEqual(len(payload['recent_posts']), 3)
