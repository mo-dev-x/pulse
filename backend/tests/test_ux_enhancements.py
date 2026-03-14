"""Automated tests for Phase 5C UX/privacy enhancements."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.phase5_test_utils import Phase5BaseTestCase


class TestUxEnhancements(Phase5BaseTestCase):

    def _verified(self, email, username):
        token, user = self.register_user(email=email, username=username)
        self.mark_verified(email)
        return token, user

    def test_privacy_preferences_and_profile_visibility(self):
        owner_token, owner = self._verified('ux1owner@ulaval.ca', 'ux1owner')
        viewer_token, _ = self._verified('ux1viewer@ulaval.ca', 'ux1viewer')

        privacy = self.client.patch(
            '/api/auth/privacy-settings',
            json={'profile_visibility': 'private', 'show_email': True},
            headers=self.auth_headers(owner_token),
        )
        self.assertEqual(privacy.status_code, 200, privacy.get_json())

        prefs = self.client.patch(
            '/api/auth/preferences',
            json={'theme': 'dark', 'email_notifications': False, 'push_notifications': True},
            headers=self.auth_headers(owner_token),
        )
        self.assertEqual(prefs.status_code, 200, prefs.get_json())

        blocked = self.client.get(f"/api/users/@{owner['username']}", headers=self.auth_headers(viewer_token))
        self.assertEqual(blocked.status_code, 403)

        mine = self.client.get('/api/auth/me', headers=self.auth_headers(owner_token))
        self.assertEqual(mine.status_code, 200)
        user_payload = mine.get_json()['user']
        self.assertEqual(user_payload['theme'], 'dark')
        self.assertEqual(user_payload['profile_visibility'], 'private')

    def test_post_pinning_and_deactivation(self):
        owner_token, owner = self._verified('ux2owner@ulaval.ca', 'ux2owner')
        follower_token, _ = self._verified('ux2follower@ulaval.ca', 'ux2follower')

        post_id = self.create_post(owner_token, content='This post will be pinned for profile display.')

        pin = self.client.patch(f'/api/posts/{post_id}/pin', headers=self.auth_headers(owner_token))
        self.assertEqual(pin.status_code, 200, pin.get_json())

        self.client.post(f"/api/follow/@{owner['username']}", headers=self.auth_headers(follower_token))
        profile = self.client.get(f"/api/users/@{owner['username']}", headers=self.auth_headers(follower_token))
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.get_json()['pinned_post']['id'], post_id)

        unpin = self.client.delete('/api/posts/pin', headers=self.auth_headers(owner_token))
        self.assertEqual(unpin.status_code, 200, unpin.get_json())

        deactivate = self.client.post('/api/auth/deactivate', headers=self.auth_headers(owner_token))
        self.assertEqual(deactivate.status_code, 200, deactivate.get_json())

        login_after = self.client.post('/api/auth/login', json={'email': owner['email'], 'password': 'SecurePass123'})
        self.assertEqual(login_after.status_code, 403)

        profile_hidden = self.client.get(f"/api/users/@{owner['username']}", headers=self.auth_headers(follower_token))
        self.assertEqual(profile_hidden.status_code, 404)

        reactivate = self.client.post('/api/auth/reactivate', headers=self.auth_headers(owner_token))
        self.assertEqual(reactivate.status_code, 200, reactivate.get_json())


if __name__ == '__main__':
    import unittest
    unittest.main()
