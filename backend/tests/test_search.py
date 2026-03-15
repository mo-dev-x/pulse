"""Automated tests for Phase 6 unified search endpoints."""

from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models import CampusZone, Post, User
from tests.phase5_test_utils import Phase5BaseTestCase


class TestSearch(Phase5BaseTestCase):

    def setUp(self):
        super().setUp()
        self.token, self.viewer = self.register_user(email='viewer@ulaval.ca', username='viewer')
        self.mark_verified('viewer@ulaval.ca')

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

        self.public_user = self._make_user('public1@ulaval.ca', 'public1', display_name='Public Library')
        self.private_user = self._make_user('private1@ulaval.ca', 'private1', display_name='Private Person', profile_visibility='private')
        self.deactivated_user = self._make_user('deactivated1@ulaval.ca', 'deactivated1', display_name='Hidden Library', is_deactivated=True)
        self.mention_user = self._make_user('bibliouser@ulaval.ca', 'bibliofan', display_name='Biblio Buddy')

        db.session.add_all([self.public_user, self.private_user, self.deactivated_user, self.mention_user])
        db.session.flush()

        self._make_post(
            self.public_user,
            'I study every day in the bibliotheque and love the calm atmosphere.',
            zone=self.zone_library,
            created_at=datetime.utcnow() - timedelta(minutes=5),
        )
        self._make_post(
            self.public_user,
            'PEPS training before class keeps my energy up.',
            zone=self.zone_peps,
            created_at=datetime.utcnow() - timedelta(minutes=4),
        )
        self._make_post(
            self.public_user,
            'bibliotheque page 1',
            zone=self.zone_library,
            created_at=datetime.utcnow() - timedelta(minutes=3),
        )
        self._make_post(
            self.public_user,
            'bibliotheque page 2',
            zone=self.zone_library,
            created_at=datetime.utcnow() - timedelta(minutes=2),
        )
        self._make_post(
            self.private_user,
            'I am private but my post is public text.',
            zone=self.zone_library,
        )
        self._make_post(
            self.deactivated_user,
            'bibliotheque content from a deactivated account',
            zone=self.zone_library,
        )
        self._make_post(
            self.public_user,
            'Anonymous bibliotheque thoughts should stay hidden.',
            zone=self.zone_library,
            is_anonymous=True,
        )
        db.session.commit()

    def _make_user(self, email, username, display_name=None, profile_visibility='public', is_deactivated=False):
        user = User(email=email, password='SecurePass123', username=username, display_name=display_name, is_verified=True)
        user.bio = f'{display_name or username} bio'
        user.profile_visibility = profile_visibility
        user.is_deactivated = is_deactivated
        return user

    def _make_post(self, user, content, zone=None, is_anonymous=False, created_at=None):
        post = Post(
            content=content,
            user_id=user.id,
            zone_id=zone.id if zone else None,
            is_anonymous=is_anonymous,
            sentiment_score=0.1,
            sentiment_label='positive',
            detected_language='en',
        )
        if created_at:
            post.created_at = created_at
        db.session.add(post)
        return post

    def test_search_returns_posts_matching_keyword(self):
        response = self.client.get('/api/search?q=bibliotheque', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertGreaterEqual(payload['counts']['posts'], 3)
        self.assertEqual(payload['results']['posts'][0]['content'], 'bibliotheque page 2')

    def test_anonymous_posts_excluded_from_search(self):
        response = self.client.get('/api/search?q=hidden', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 200, response.get_json())
        contents = [post['content'] for post in response.get_json()['results']['posts']]
        self.assertNotIn('Anonymous bibliotheque thoughts should stay hidden.', contents)

    def test_private_profile_users_excluded_from_search(self):
        response = self.client.get('/api/search?q=private', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()['counts']['users'], 0)

    def test_deactivated_users_excluded_from_search(self):
        response = self.client.get('/api/search?q=hidden', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertEqual(payload['counts']['users'], 0)
        contents = [post['content'] for post in payload['results']['posts']]
        self.assertNotIn('bibliotheque content from a deactivated account', contents)

    def test_type_users_returns_only_users(self):
        response = self.client.get('/api/search?q=biblio&type=users', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertGreaterEqual(payload['counts']['users'], 1)
        self.assertEqual(payload['counts']['posts'], 0)
        self.assertEqual(payload['counts']['zones'], 0)

    def test_type_zones_returns_only_zones(self):
        response = self.client.get('/api/search?q=peps&type=zones', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertEqual(payload['counts']['zones'], 1)
        self.assertEqual(payload['results']['zones'][0]['name'], 'PEPS - Pavillon principal')
        self.assertEqual(payload['counts']['posts'], 0)

    def test_query_under_two_chars_returns_400(self):
        response = self.client.get('/api/search?q=b', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 400)

    def test_missing_q_param_returns_400(self):
        response = self.client.get('/api/search', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 400)

    def test_pagination_works_correctly(self):
        response = self.client.get('/api/search?q=bibliotheque&type=posts&per_page=2&page=1', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertEqual(len(payload['results']['posts']), 2)
        self.assertTrue(payload['has_next'])

        page_two = self.client.get('/api/search?q=bibliotheque&type=posts&per_page=2&page=2', headers=self.auth_headers(self.token))
        self.assertEqual(page_two.status_code, 200, page_two.get_json())
        self.assertGreaterEqual(len(page_two.get_json()['results']['posts']), 1)

    def test_user_only_search_endpoint_works_for_mentions(self):
        response = self.client.get('/api/search/users?q=biblio&limit=5', headers=self.auth_headers(self.token))
        self.assertEqual(response.status_code, 200, response.get_json())
        users = response.get_json()['users']
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['username'], 'bibliofan')

