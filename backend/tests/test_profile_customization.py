"""Automated tests for Phase 5A profile customization endpoints."""

import io
from pathlib import Path
import sys
from unittest.mock import patch

# Ensure `app` imports resolve when tests are run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.user import User
from tests.phase5_test_utils import Phase5BaseTestCase


class TestProfileCustomization(Phase5BaseTestCase):
    @staticmethod
    def _fake_resize(stream, path, size):
        _ = size
        with open(path, 'wb') as file_obj:
            file_obj.write(stream.read())

    def test_update_bio_success(self):
        token, _ = self.register_user(email='profile1@ulaval.ca', username='profile1')
        response = self.client.patch(
            '/api/auth/update-bio',
            json={'bio': 'I study engineering at ULaval.'},
            headers=self.auth_headers(token)
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        user = User.query.filter_by(email='profile1@ulaval.ca').first()
        self.assertEqual(user.bio, 'I study engineering at ULaval.')

    def test_update_bio_validation(self):
        token, _ = self.register_user(email='profile2@ulaval.ca', username='profile2')
        response = self.client.patch(
            '/api/auth/update-bio',
            json={'bio': 'a' * 501},
            headers=self.auth_headers(token)
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_profile_picture_success(self):
        token, _ = self.register_user(email='profile3@ulaval.ca', username='profile3')
        image = self.image_file()
        with patch('app.routes.auth._resize_and_save_image') as mock_resize:
            mock_resize.side_effect = self._fake_resize
            response = self.client.post(
                '/api/auth/upload-profile-pic',
                data={'file': (image, 'avatar.png')},
                headers=self.auth_headers(token),
                content_type='multipart/form-data'
            )
        self.assertEqual(response.status_code, 200, response.get_json())
        user = User.query.filter_by(email='profile3@ulaval.ca').first()
        self.assertTrue(user.profile_picture.startswith('profiles/'))

    def test_upload_header_success(self):
        token, _ = self.register_user(email='profile4@ulaval.ca', username='profile4')
        image = self.image_file()
        with patch('app.routes.auth._resize_and_save_image') as mock_resize:
            mock_resize.side_effect = self._fake_resize
            response = self.client.post(
                '/api/auth/upload-header',
                data={'file': (image, 'header.png')},
                headers=self.auth_headers(token),
                content_type='multipart/form-data'
            )
        self.assertEqual(response.status_code, 200, response.get_json())
        user = User.query.filter_by(email='profile4@ulaval.ca').first()
        self.assertTrue(user.header_image.startswith('headers/'))

    def test_upload_rejects_invalid_type(self):
        token, _ = self.register_user(email='profile5@ulaval.ca', username='profile5')
        file_data = io.BytesIO(b'not an image')
        response = self.client.post(
            '/api/auth/upload-profile-pic',
            data={'file': (file_data, 'note.txt')},
            headers=self.auth_headers(token),
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_rejects_oversized_file(self):
        token, _ = self.register_user(email='profile6@ulaval.ca', username='profile6')
        large_data = io.BytesIO(b'x' * (5 * 1024 * 1024 + 10))
        response = self.client.post(
            '/api/auth/upload-profile-pic',
            data={'file': (large_data, 'big.jpg')},
            headers=self.auth_headers(token),
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 413)


if __name__ == '__main__':
    import unittest
    unittest.main()
