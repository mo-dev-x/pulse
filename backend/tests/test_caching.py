"""Automated tests for Phase 6 caching layer."""

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import cache, db
from app.models import CampusZone, Post, Reaction
from tests.phase5_test_utils import Phase5BaseTestCase


class TestCaching(Phase5BaseTestCase):

    def setUp(self):
        super().setUp()
        cache.clear()
        self.token, _ = self.register_user(email='cache_viewer@ulaval.ca', username='cache_viewer')
        self.mark_verified('cache_viewer@ulaval.ca')

    def test_zones_endpoint_uses_cache(self):
        db.session.add(CampusZone(name='Zone A', description='First', zone_type='academic'))
        db.session.commit()

        first = self.client.get('/api/zones')
        self.assertEqual(first.status_code, 200, first.get_json())
        self.assertEqual(first.get_json()['count'], 1)

        db.session.add(CampusZone(name='Zone B', description='Second', zone_type='sports'))
        db.session.commit()

        second = self.client.get('/api/zones')
        self.assertEqual(second.status_code, 200, second.get_json())
        self.assertEqual(second.get_json()['count'], 1)

    def test_posts_trending_endpoint_uses_cache(self):
        owner_token, _ = self.register_user(email='cache_owner@ulaval.ca', username='cache_owner')
        self.mark_verified('cache_owner@ulaval.ca')
        zone = CampusZone(name='Zone Trend', description='Trending', zone_type='academic')
        db.session.add(zone)
        db.session.commit()

        self.create_post(owner_token, content='Trending cache post with enough characters.')
        first = self.client.get('/api/posts/trending', headers=self.auth_headers(self.token))
        self.assertEqual(first.status_code, 200, first.get_json())

        self.create_post(owner_token, content='Second trending cache post with enough characters.')
        second = self.client.get('/api/posts/trending', headers=self.auth_headers(self.token))
        self.assertEqual(second.status_code, 200, second.get_json())
        self.assertEqual(len(second.get_json()['posts']), len(first.get_json()['posts']))

    def test_trending_cache_is_scoped_per_user(self):
        owner_token, _ = self.register_user(email='cache_scope_owner@ulaval.ca', username='cache_scope_owner')
        self.mark_verified('cache_scope_owner@ulaval.ca')
        other_token, _ = self.register_user(email='cache_scope_other@ulaval.ca', username='cache_scope_other')
        self.mark_verified('cache_scope_other@ulaval.ca')

        with patch('app.routes.posts.analyze_sentiment', return_value={
            'score': 0.1,
            'label': 'positive',
            'language': 'en',
        }):
            created = self.client.post(
                '/api/posts',
                json={'content': 'Trending cache scope post with enough characters.', 'is_anonymous': False},
                headers=self.auth_headers(owner_token),
            )
        self.assertEqual(created.status_code, 201, created.get_json())
        post_id = created.get_json()['post']['id']

        db.session.add(Reaction(post_id=post_id, user_id=self.get_user('cache_viewer@ulaval.ca').id, emoji='❤️'))
        db.session.commit()

        first = self.client.get('/api/posts/trending', headers=self.auth_headers(self.token))
        self.assertEqual(first.status_code, 200, first.get_json())
        self.assertEqual(first.get_json()['posts'][0]['my_reaction'], '❤️')

        second = self.client.get('/api/posts/trending', headers=self.auth_headers(other_token))
        self.assertEqual(second.status_code, 200, second.get_json())
        self.assertIsNone(second.get_json()['posts'][0]['my_reaction'])

    def test_public_profile_base_payload_is_cached(self):
        owner_token, owner = self.register_user(email='cache_profile@ulaval.ca', username='cache_profile')
        self.mark_verified('cache_profile@ulaval.ca')
        self.client.patch(
            '/api/auth/update-profile',
            json={'bio': 'Original bio'},
            headers=self.auth_headers(owner_token),
        )

        first = self.client.get(f"/api/users/@{owner['username']}", headers=self.auth_headers(self.token))
        self.assertEqual(first.status_code, 200, first.get_json())
        self.assertEqual(first.get_json()['user']['bio'], 'Original bio')

        self.client.patch(
            '/api/auth/update-profile',
            json={'bio': 'Updated bio'},
            headers=self.auth_headers(owner_token),
        )
        second = self.client.get(f"/api/users/@{owner['username']}", headers=self.auth_headers(self.token))
        self.assertEqual(second.status_code, 200, second.get_json())
        self.assertEqual(second.get_json()['user']['bio'], 'Original bio')
