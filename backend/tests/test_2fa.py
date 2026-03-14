"""Automated tests for Phase 5C 2FA and security logs."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.security_log import SecurityLog
from app.models.user import User
from app.services.totp_service import generate_totp
from tests.phase5_test_utils import Phase5BaseTestCase


class TestTwoFactorAndSecurityLogs(Phase5BaseTestCase):

    def _verified(self, email='tfa1@ulaval.ca', username='tfa1'):
        token, user = self.register_user(email=email, username=username)
        self.mark_verified(email)
        return token, user

    def test_enable_verify_disable_and_backup_codes(self):
        token, user = self._verified('tfa2@ulaval.ca', 'tfa2')

        enable = self.client.post('/api/auth/2fa/enable', headers=self.auth_headers(token))
        self.assertEqual(enable.status_code, 200, enable.get_json())
        payload = enable.get_json()
        self.assertIn('totp_secret', payload)
        self.assertEqual(len(payload['backup_codes']), 10)

        code = generate_totp(payload['totp_secret'])
        verify = self.client.post('/api/auth/2fa/verify', json={'code': code}, headers=self.auth_headers(token))
        self.assertEqual(verify.status_code, 200, verify.get_json())
        self.assertIsNotNone(SecurityLog.query.filter_by(event_type='2fa_enabled').first())

        user_row = User.query.filter_by(email=user['email']).first()
        self.assertTrue(user_row.totp_enabled)

        regen = self.client.get('/api/auth/2fa/backup-codes', headers=self.auth_headers(token))
        self.assertEqual(regen.status_code, 200, regen.get_json())
        self.assertEqual(len(regen.get_json()['backup_codes']), 10)

        backup_code = regen.get_json()['backup_codes'][0]
        disable = self.client.post('/api/auth/2fa/disable', json={'backup_code': backup_code}, headers=self.auth_headers(token))
        self.assertEqual(disable.status_code, 200, disable.get_json())
        self.assertIsNotNone(SecurityLog.query.filter_by(event_type='2fa_disabled').first())

    def test_login_flow_requires_2fa_when_enabled(self):
        token, user = self._verified('tfa3@ulaval.ca', 'tfa3')

        enable = self.client.post('/api/auth/2fa/enable', headers=self.auth_headers(token)).get_json()
        code = generate_totp(enable['totp_secret'])
        self.client.post('/api/auth/2fa/verify', json={'code': code}, headers=self.auth_headers(token))

        no_2fa = self.client.post('/api/auth/login', json={'email': user['email'], 'password': 'SecurePass123'})
        self.assertEqual(no_2fa.status_code, 401)
        self.assertTrue(no_2fa.get_json().get('requires_2fa'))

        login_code = generate_totp(enable['totp_secret'])
        with_2fa = self.client.post('/api/auth/login', json={
            'email': user['email'],
            'password': 'SecurePass123',
            'totp_code': login_code,
        })
        self.assertEqual(with_2fa.status_code, 200, with_2fa.get_json())

    def test_security_logs_written_for_login_fail_and_2fa_events(self):
        _, user = self._verified('tfa4@ulaval.ca', 'tfa4')

        bad_login = self.client.post('/api/auth/login', json={'email': user['email'], 'password': 'WrongPass123'})
        self.assertEqual(bad_login.status_code, 401)
        self.assertIsNotNone(SecurityLog.query.filter_by(event_type='login_failed').first())


if __name__ == '__main__':
    unittest.main()
