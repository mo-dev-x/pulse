"""Automated tests for Phase 5B session management."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask_jwt_extended import decode_token

from app.models.session import Session
from tests.phase5_test_utils import Phase5BaseTestCase


class TestSessions(Phase5BaseTestCase):

    def _verified_user(self, email='sess1@ulaval.ca', username='sess1'):
        token, user = self.register_user(email=email, username=username)
        self.mark_verified(email)
        return token, user

    def test_login_tracks_sessions_and_list_endpoint(self):
        _, user = self._verified_user('sess2@ulaval.ca', 'sess2')
        login = self.client.post('/api/auth/login', json={'email': user['email'], 'password': 'SecurePass123'})
        self.assertEqual(login.status_code, 200, login.get_json())
        token = login.get_json()['token']

        listing = self.client.get('/api/auth/sessions', headers=self.auth_headers(token))
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()['total'], 1)

        db_sessions = Session.query.filter_by(user_id=user['id']).all()
        self.assertGreaterEqual(len(db_sessions), 1)

    def test_revoke_single_and_all_sessions(self):
        register_token, user = self._verified_user('sess3@ulaval.ca', 'sess3')
        login = self.client.post('/api/auth/login', json={'email': user['email'], 'password': 'SecurePass123'})
        self.assertEqual(login.status_code, 200, login.get_json())
        login_token = login.get_json()['token']

        listing = self.client.get('/api/auth/sessions', headers=self.auth_headers(login_token)).get_json()['sessions']
        self.assertGreaterEqual(len(listing), 2)

        current_jti = decode_token(login_token)['jti']
        other_session = next(s for s in listing if s['token_jti'] != current_jti)
        revoke_one = self.client.delete(f"/api/auth/sessions/{other_session['id']}", headers=self.auth_headers(login_token))
        self.assertEqual(revoke_one.status_code, 200, revoke_one.get_json())

        revoke_all = self.client.delete('/api/auth/sessions/all', headers=self.auth_headers(login_token))
        self.assertEqual(revoke_all.status_code, 200, revoke_all.get_json())

        active_count = Session.query.filter_by(user_id=user['id'], is_active=True).count()
        self.assertEqual(active_count, 1)

        # register token should be blocked after revocation
        blocked = self.client.get('/api/auth/me', headers=self.auth_headers(register_token))
        self.assertEqual(blocked.status_code, 401)

    def test_logout_revokes_current_session(self):
        _, user = self._verified_user('sess4@ulaval.ca', 'sess4')
        login = self.client.post('/api/auth/login', json={'email': user['email'], 'password': 'SecurePass123'})
        token = login.get_json()['token']

        logout = self.client.post('/api/auth/logout', headers=self.auth_headers(token))
        self.assertEqual(logout.status_code, 200)

        denied = self.client.get('/api/auth/me', headers=self.auth_headers(token))
        self.assertEqual(denied.status_code, 401)


if __name__ == '__main__':
    import unittest
    unittest.main()
