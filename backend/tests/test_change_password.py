"""Automated tests for authenticated password changes."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.phase5_test_utils import Phase5BaseTestCase


class TestChangePassword(Phase5BaseTestCase):

    def test_change_password_requires_current_password_and_updates_login_credentials(self):
        token, user = self.register_user(email='changepw@ulaval.ca', username='changepw')
        self.mark_verified('changepw@ulaval.ca')

        response = self.client.post(
            '/api/auth/change-password',
            json={
                'current_password': 'SecurePass123',
                'new_password': 'BetterPass456',
            },
            headers=self.auth_headers(token),
        )

        self.assertEqual(response.status_code, 200, response.get_json())

        old_login = self.client.post('/api/auth/login', json={
            'email': user['email'],
            'password': 'SecurePass123',
        })
        self.assertEqual(old_login.status_code, 401, old_login.get_json())

        new_login = self.client.post('/api/auth/login', json={
            'email': user['email'],
            'password': 'BetterPass456',
        })
        self.assertEqual(new_login.status_code, 200, new_login.get_json())


if __name__ == '__main__':
    import unittest
    unittest.main()
