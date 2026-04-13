"""
Cloudinary Upload Utility

Centralizes all file uploads to Cloudinary.
Uses resource_type="auto" so both images and audio are handled transparently.

Usage:
    url, error = upload_to_cloudinary(file_obj, folder="posts")
    if error:
        return jsonify({'error': error}), 400
"""

import cloudinary
import cloudinary.uploader
from flask import current_app


def _init_cloudinary():
    """Configure Cloudinary from Flask app config (called lazily per request)."""
    cloudinary.config(
        cloud_name=current_app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=current_app.config.get('CLOUDINARY_API_KEY'),
        api_secret=current_app.config.get('CLOUDINARY_API_SECRET'),
        secure=True,
    )


def upload_to_cloudinary(file_obj, folder="uploads", public_id=None, **kwargs):
    """
    Upload a file-like object or stream to Cloudinary.

    Args:
        file_obj: A file-like object (werkzeug FileStorage, BytesIO, etc.)
        folder:   Cloudinary folder name (e.g. "posts", "profiles", "messages")
        public_id: Optional explicit public_id; auto-generated when omitted.
        **kwargs: Extra options forwarded to cloudinary.uploader.upload()

    Returns:
        (secure_url, None)  on success
        (None, error_str)   on failure
    """
    _init_cloudinary()

    upload_options = {
        'folder': folder,
        'resource_type': 'auto',   # handles images, audio, video, raw
        'overwrite': False,
        **kwargs,
    }
    if public_id:
        upload_options['public_id'] = public_id

    try:
        result = cloudinary.uploader.upload(file_obj, **upload_options)
        return result.get('secure_url'), None
    except cloudinary.exceptions.Error as exc:
        current_app.logger.error('Cloudinary upload failed: %s', exc)
        return None, f'Upload failed: {exc}'
    except Exception as exc:
        current_app.logger.error('Unexpected error during Cloudinary upload: %s', exc)
        return None, 'Upload failed due to an unexpected error'


def is_cloudinary_configured():
    """Return True if all three Cloudinary credentials are present."""
    return bool(
        current_app.config.get('CLOUDINARY_CLOUD_NAME')
        and current_app.config.get('CLOUDINARY_API_KEY')
        and current_app.config.get('CLOUDINARY_API_SECRET')
    )
