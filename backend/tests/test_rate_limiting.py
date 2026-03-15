"""Automated tests for Phase 6 rate limiting."""

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models import CampusZone
from tests.phase5_test_utils import Phase5BaseTestCase


class TestRateLimiting(Phase5BaseTestCase):

    def setUp(self):
        super().setUp()
        self.app.config.update(
            LOGIN_RATE_LIMIT='2 per minute',
            SEARCH_RATE_LIMIT='3 per minute',
            POST_CREATE_RATE_LIMIT='2 per hour',
            COMMENT_CREATE_RATE_LIMIT='2 per hour',
            REACTION_RATE_LIMIT='2 per minute',
        )

        zone = CampusZone(
            name='Pavillon Jean-Charles-Bonenfant',
            description='Bibliotheque principale',
            zone_type='academic',
        )
        db.session.add(zone)
        db.session.commit()
        self.zone_id = zone.id

    def _verified_user(self, email, username):
        token, user = self.register_user(email=email, username=username)
        self.mark_verified(email)
        return token, user

    def test_login_rate_limit_triggers_after_limit(self):
        _, user = self._verified_user('limit_login@ulaval.ca', 'limit_login')
        for _ in range(2):
            response = self.client.post('/api/auth/login', json={'email': user['email'], 'password': 'wrong-password'})
            self.assertEqual(response.status_code, 401)

        limited = self.client.post('/api/auth/login', json={'email': user['email'], 'password': 'wrong-password'})
        self.assertEqual(limited.status_code, 429)

    def test_rate_limit_returns_429_with_retry_after_body(self):
        token, _ = self._verified_user('limit_search@ulaval.ca', 'limit_search')
        for _ in range(3):
            response = self.client.get('/api/search?q=li', headers=self.auth_headers(token))
            self.assertEqual(response.status_code, 200, response.get_json())

        limited = self.client.get('/api/search?q=li', headers=self.auth_headers(token))
        self.assertEqual(limited.status_code, 429)
        payload = limited.get_json()
        self.assertTrue(payload['error'])
        self.assertTrue(payload['message'])
        self.assertIn('retry_after', payload)

    def test_different_users_have_independent_write_limits(self):
        token_a, _ = self._verified_user('limit_a@ulaval.ca', 'limit_a')
        token_b, _ = self._verified_user('limit_b@ulaval.ca', 'limit_b')

        with patch('app.routes.posts.analyze_sentiment', return_value={'score': 0.2, 'label': 'positive', 'language': 'en'}):
            for index in range(2):
                response = self.client.post(
                    '/api/posts',
                    json={'content': f'User A post number {index} with enough characters.', 'zone_id': self.zone_id, 'is_anonymous': False},
                    headers=self.auth_headers(token_a),
                )
                self.assertEqual(response.status_code, 201, response.get_json())

            limited = self.client.post(
                '/api/posts',
                json={'content': 'User A should hit the post rate limit now.', 'zone_id': self.zone_id, 'is_anonymous': False},
                headers=self.auth_headers(token_a),
            )
            self.assertEqual(limited.status_code, 429)

            other_user = self.client.post(
                '/api/posts',
                json={'content': 'User B should still be allowed to post right now.', 'zone_id': self.zone_id, 'is_anonymous': False},
                headers=self.auth_headers(token_b),
            )
            self.assertEqual(other_user.status_code, 201, other_user.get_json())
