"""Shared test utilities for Phase 5A automated tests."""

import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure `app` imports resolve when tests are run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models.user import User


class Phase5BaseTestCase(unittest.TestCase):
    """Base test case with isolated in-memory DB and temp upload folders."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app('testing')
        self.app.config.update(
            FRONTEND_URL='http://localhost:3000',
            UPLOAD_FOLDER=self.temp_dir.name,
            PROFILE_UPLOAD_FOLDER=os.path.join(self.temp_dir.name, 'profiles'),
            HEADER_UPLOAD_FOLDER=os.path.join(self.temp_dir.name, 'headers'),
            SMTP_HOST=None,
            BACKGROUND_JOBS_ENABLED=False,
            BACKGROUND_JOBS_EAGER=True,
        )

        os.makedirs(self.app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(self.app.config['HEADER_UPLOAD_FOLDER'], exist_ok=True)

        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        self.temp_dir.cleanup()

    def register_user(self, email='user@ulaval.ca', password='SecurePass123', username='user1'):
        response = self.client.post('/api/auth/register', json={
            'email': email,
            'password': password,
            'username': username,
            'display_name': username
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        data = response.get_json()
        return data['token'], data['user']

    def auth_headers(self, token):
        return {'Authorization': f'Bearer {token}'}

    def mark_verified(self, email):
        user = User.query.filter_by(email=email).first()
        user.is_verified = True
        user.verification_token = None
        user.verification_expires = None
        db.session.commit()
        return user

    def get_user(self, email):
        return User.query.filter_by(email=email).first()

    def create_post(self, token, content='This is a verified post with enough chars.'):
        with patch('app.routes.posts.analyze_sentiment', return_value={
            'score': 0.1,
            'label': 'positive',
            'language': 'en'
        }):
            response = self.client.post(
                '/api/posts',
                json={'content': content, 'is_anonymous': False},
                headers=self.auth_headers(token)
            )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()['post']['id']

    def image_file(self):
        # Minimal valid 1x1 PNG binary to avoid test dependency on Pillow.
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
            b"\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01"
            b"\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return io.BytesIO(png_bytes)
