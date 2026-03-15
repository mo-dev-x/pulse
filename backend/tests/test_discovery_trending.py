"""Automated tests for Phase 6 discovery and trending endpoints."""

from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models import CampusZone, Comment, Post, Reaction, User
from tests.phase5_test_utils import Phase5BaseTestCase


class TestDiscoveryTrending(Phase5BaseTestCase):

    def setUp(self):
        super().setUp()
        self.viewer_token, _ = self.register_user(email='discover_viewer@ulaval.ca', username='discover_viewer')
        self.mark_verified('discover_viewer@ulaval.ca')

        self.zone_library = CampusZone(
            name='Pavillon Jean-Charles-Bonenfant',
            description='Bibliotheque principale',
            zone_type='academic',
        )
        self.zone_peps = CampusZone(
            name='PEPS - Pavillon principal',
            description='Centre sportif principal',
            zone_type='sports',
        )
        db.session.add_all([self.zone_library, self.zone_peps])
        db.session.flush()

        self.author = self._make_user('discover_author@ulaval.ca', 'discover_author', is_verified=True)
        self.unverified_author = self._make_user('discover_unverified@ulaval.ca', 'discover_unverified', is_verified=False)
        self.deactivated_author = self._make_user('discover_deactivated@ulaval.ca', 'discover_deactivated', is_verified=True, is_deactivated=True)
        self.reactor = self._make_user('discover_reactor@ulaval.ca', 'discover_reactor', is_verified=True)
        self.commenter = self._make_user('discover_commenter@ulaval.ca', 'discover_commenter', is_verified=True)
        db.session.add_all([self.author, self.unverified_author, self.deactivated_author, self.reactor, self.commenter])
        db.session.flush()

        self.top_post = self._make_post(
            self.author,
            'Library post with strong engagement and enough characters.',
            zone=self.zone_library,
            sentiment_score=0.7,
            created_at=datetime.utcnow() - timedelta(hours=1),
        )
        self.mid_post = self._make_post(
            self.author,
            'Another library discovery post with enough characters.',
            zone=self.zone_library,
            sentiment_score=0.4,
            created_at=datetime.utcnow() - timedelta(hours=3),
        )
        self.sports_post = self._make_post(
            self.author,
            'PEPS workout post with enough characters for testing.',
            zone=self.zone_peps,
            sentiment_score=0.2,
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        self.old_post = self._make_post(
            self.author,
            'Old public post outside the short trending window.',
            zone=self.zone_peps,
            sentiment_score=-0.4,
            created_at=datetime.utcnow() - timedelta(days=2),
        )
        self._make_post(
            self.author,
            'Anonymous campus thought that should not appear in discovery.',
            zone=self.zone_library,
            is_anonymous=True,
            created_at=datetime.utcnow() - timedelta(minutes=30),
        )
        self._make_post(
            self.unverified_author,
            'Unverified author post should never appear in discovery feeds.',
            zone=self.zone_library,
            created_at=datetime.utcnow() - timedelta(minutes=20),
        )
        self._make_post(
            self.deactivated_author,
            'Deactivated author post should never appear in discovery feeds.',
            zone=self.zone_library,
            created_at=datetime.utcnow() - timedelta(minutes=10),
        )
        db.session.flush()

        self._react(self.top_post, self.reactor, '❤️')
        self._react(self.top_post, self.commenter, '🔥')
        self._comment(self.top_post, self.commenter, 'Top post comment')

        self._react(self.mid_post, self.reactor, '❤️')
        self._comment(self.mid_post, self.commenter, 'Mid post comment')

        self._react(self.sports_post, self.reactor, '❤️')
        db.session.commit()

    def _make_user(self, email, username, is_verified=True, is_deactivated=False):
        user = User(email=email, password='SecurePass123', username=username, display_name=username, is_verified=is_verified)
        user.is_deactivated = is_deactivated
        return user

    def _make_post(self, user, content, zone=None, sentiment_score=0.1, is_anonymous=False, created_at=None):
        post = Post(
            content=content,
            user_id=user.id,
            zone_id=zone.id if zone else None,
            is_anonymous=is_anonymous,
            sentiment_score=sentiment_score,
            sentiment_label='positive' if sentiment_score > 0.15 else 'negative' if sentiment_score < -0.15 else 'neutral',
            detected_language='en',
        )
        if created_at:
            post.created_at = created_at
        db.session.add(post)
        return post

    def _react(self, post, user, emoji):
        db.session.add(Reaction(post_id=post.id, user_id=user.id, emoji=emoji))

    def _comment(self, post, user, content):
        db.session.add(Comment(post_id=post.id, user_id=user.id, content=content, is_anonymous=False))

    def test_discovery_feed_returns_public_posts_only(self):
        response = self.client.get('/api/posts/discover', headers=self.auth_headers(self.viewer_token))
        self.assertEqual(response.status_code, 200, response.get_json())
        posts = response.get_json()['posts']
        self.assertTrue(posts)
        for post in posts:
            self.assertFalse(post['is_anonymous'])

    def test_anonymous_posts_excluded_from_discovery(self):
        response = self.client.get('/api/posts/discover', headers=self.auth_headers(self.viewer_token))
        contents = [post['content'] for post in response.get_json()['posts']]
        self.assertNotIn('Anonymous campus thought that should not appear in discovery.', contents)

    def test_zone_filter_works_on_discovery(self):
        response = self.client.get(
            f'/api/posts/discover?zone_id={self.zone_peps.id}',
            headers=self.auth_headers(self.viewer_token),
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        posts = response.get_json()['posts']
        self.assertEqual(len(posts), 2)
        self.assertTrue(all(post['zone']['id'] == self.zone_peps.id for post in posts))

    def test_trending_returns_posts_ordered_by_engagement(self):
        response = self.client.get('/api/posts/trending?window=24h', headers=self.auth_headers(self.viewer_token))
        self.assertEqual(response.status_code, 200, response.get_json())
        posts = response.get_json()['posts']
        self.assertGreaterEqual(len(posts), 3)
        self.assertEqual(posts[0]['id'], self.top_post.id)

    def test_time_window_filtering_works(self):
        response = self.client.get('/api/posts/trending?window=1h', headers=self.auth_headers(self.viewer_token))
        self.assertEqual(response.status_code, 200, response.get_json())
        posts = response.get_json()['posts']
        self.assertEqual(len(posts), 0)

        response_24h = self.client.get('/api/posts/trending?window=24h', headers=self.auth_headers(self.viewer_token))
        self.assertEqual(response_24h.status_code, 200, response_24h.get_json())
        ids = [post['id'] for post in response_24h.get_json()['posts']]
        self.assertNotIn(self.old_post.id, ids)

    def test_empty_result_when_no_posts_in_window(self):
        response = self.client.get('/api/posts/trending?window=1h&zone_id=999', headers=self.auth_headers(self.viewer_token))
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertEqual(payload['posts'], [])
        self.assertEqual(payload['trending_zones'], [])

    def test_trending_zones_returns_correct_counts(self):
        response = self.client.get('/api/zones/trending?window=24h')
        self.assertEqual(response.status_code, 200, response.get_json())
        zones = response.get_json()['zones']
        self.assertGreaterEqual(len(zones), 2)
        self.assertEqual(zones[0]['zone']['id'], self.zone_library.id)
        self.assertEqual(zones[0]['post_count'], 2)
