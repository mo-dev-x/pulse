"""Automated tests for Phase 6 moderation and reporting."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models import Comment, Post, Report, SecurityLog, User
from tests.phase5_test_utils import Phase5BaseTestCase


class TestReports(Phase5BaseTestCase):

    def _verified_user(self, email, username, is_admin=False):
        token, user = self.register_user(email=email, username=username)
        db_user = self.mark_verified(email)
        db_user.is_admin = is_admin
        db.session.commit()
        return token, user

    def _create_comment(self, token, post_id, content='Reportable comment'):
        response = self.client.post(
            f'/api/posts/{post_id}/comments',
            json={'content': content},
            headers=self.auth_headers(token)
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()['comment']['id']

    def test_submit_report_success(self):
        owner_token, _ = self._verified_user('report_owner@ulaval.ca', 'report_owner')
        reporter_token, _ = self._verified_user('report_reporter@ulaval.ca', 'report_reporter')
        post_id = self.create_post(owner_token, content='This post can be reported because it is long enough.')

        response = self.client.post(
            '/api/reports',
            json={'target_type': 'post', 'target_id': post_id, 'reason': 'spam', 'details': 'Looks suspicious'},
            headers=self.auth_headers(reporter_token),
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(Report.query.count(), 1)

    def test_duplicate_report_returns_409(self):
        owner_token, _ = self._verified_user('report_dup_owner@ulaval.ca', 'report_dup_owner')
        reporter_token, _ = self._verified_user('report_dup_reporter@ulaval.ca', 'report_dup_reporter')
        post_id = self.create_post(owner_token, content='Duplicate report target with enough text.')

        payload = {'target_type': 'post', 'target_id': post_id, 'reason': 'spam'}
        first = self.client.post('/api/reports', json=payload, headers=self.auth_headers(reporter_token))
        self.assertEqual(first.status_code, 201, first.get_json())

        second = self.client.post('/api/reports', json=payload, headers=self.auth_headers(reporter_token))
        self.assertEqual(second.status_code, 409)

    def test_cannot_report_own_content(self):
        owner_token, _ = self._verified_user('report_self@ulaval.ca', 'report_self')
        post_id = self.create_post(owner_token, content='Self report target with enough characters.')

        response = self.client.post(
            '/api/reports',
            json={'target_type': 'post', 'target_id': post_id, 'reason': 'other'},
            headers=self.auth_headers(owner_token),
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_can_list_pending_reports(self):
        owner_token, _ = self._verified_user('report_list_owner@ulaval.ca', 'report_list_owner')
        reporter_token, _ = self._verified_user('report_list_reporter@ulaval.ca', 'report_list_reporter')
        admin_token, _ = self._verified_user('report_list_admin@ulaval.ca', 'report_list_admin', is_admin=True)
        post_id = self.create_post(owner_token, content='Pending report target with enough characters.')
        self.client.post('/api/reports', json={'target_type': 'post', 'target_id': post_id, 'reason': 'spam'}, headers=self.auth_headers(reporter_token))

        response = self.client.get('/api/admin/reports', headers=self.auth_headers(admin_token))
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()['total'], 1)

    def test_admin_hide_content_sets_flags_and_logs(self):
        owner_token, _ = self._verified_user('report_hide_owner@ulaval.ca', 'report_hide_owner')
        reporter_token, _ = self._verified_user('report_hide_reporter@ulaval.ca', 'report_hide_reporter')
        admin_token, _ = self._verified_user('report_hide_admin@ulaval.ca', 'report_hide_admin', is_admin=True)
        post_id = self.create_post(owner_token, content='Hide me please because this is moderation test content.')
        report = self.client.post(
            '/api/reports',
            json={'target_type': 'post', 'target_id': post_id, 'reason': 'harassment'},
            headers=self.auth_headers(reporter_token),
        ).get_json()

        action = self.client.patch(
            f"/api/admin/reports/{report['report_id']}",
            json={'action': 'hide_content'},
            headers=self.auth_headers(admin_token),
        )
        self.assertEqual(action.status_code, 200, action.get_json())
        post = Post.query.get(post_id)
        self.assertTrue(post.hidden_by_mod)
        self.assertTrue(post.is_flagged)
        self.assertIsNotNone(SecurityLog.query.filter_by(event_type='content_hidden_by_admin').first())

    def test_admin_can_deactivate_user_from_report(self):
        owner_token, owner = self._verified_user('report_user_owner@ulaval.ca', 'report_user_owner')
        reporter_token, _ = self._verified_user('report_user_reporter@ulaval.ca', 'report_user_reporter')
        admin_token, _ = self._verified_user('report_user_admin@ulaval.ca', 'report_user_admin', is_admin=True)

        report = self.client.post(
            '/api/reports',
            json={'target_type': 'user', 'target_id': owner['id'], 'reason': 'other'},
            headers=self.auth_headers(reporter_token),
        ).get_json()
        action = self.client.patch(
            f"/api/admin/reports/{report['report_id']}",
            json={'action': 'deactivate_user'},
            headers=self.auth_headers(admin_token),
        )
        self.assertEqual(action.status_code, 200, action.get_json())
        db_user = User.query.get(owner['id'])
        self.assertTrue(db_user.is_deactivated)
        self.assertIsNotNone(SecurityLog.query.filter_by(event_type='user_deactivated_by_admin').first())

    def test_auto_flagged_posts_appear_in_flagged_queue(self):
        owner_token, _ = self._verified_user('report_flag_owner@ulaval.ca', 'report_flag_owner')
        admin_token, _ = self._verified_user('report_flag_admin@ulaval.ca', 'report_flag_admin', is_admin=True)
        post_id = self.create_post(owner_token, content='This post will be auto flagged after enough reports.')

        for idx in range(5):
            reporter_token, _ = self._verified_user(f'report_flag_{idx}@ulaval.ca', f'report_flag_{idx}')
            response = self.client.post(
                '/api/reports',
                json={'target_type': 'post', 'target_id': post_id, 'reason': 'spam'},
                headers=self.auth_headers(reporter_token),
            )
            self.assertEqual(response.status_code, 201, response.get_json())

        flagged = self.client.get('/api/admin/flagged', headers=self.auth_headers(admin_token))
        self.assertEqual(flagged.status_code, 200, flagged.get_json())
        payload = flagged.get_json()
        self.assertEqual(payload['total'], 1)
        self.assertEqual(payload['posts'][0]['id'], post_id)

    def test_admin_can_delete_post(self):
        owner_token, _ = self._verified_user('report_delete_owner@ulaval.ca', 'report_delete_owner')
        admin_token, _ = self._verified_user('report_delete_admin@ulaval.ca', 'report_delete_admin', is_admin=True)
        post_id = self.create_post(owner_token, content='Delete this moderated post with enough text.')

        response = self.client.delete(f'/api/admin/posts/{post_id}', headers=self.auth_headers(admin_token))
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertIsNone(Post.query.get(post_id))

