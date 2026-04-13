"""
Generic Upload Endpoint

POST /api/upload
  - Accepts multipart/form-data with a 'file' field
  - Uploads to Cloudinary using resource_type="auto" (images + audio)
  - Returns { "url": "<cloudinary_secure_url>", "resource_type": "image|video|raw" }

The frontend can call this endpoint to get a Cloudinary URL and then
include that URL in subsequent API calls (e.g. when creating a post or message).
"""

import uuid
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.utils.cloudinary_utils import upload_to_cloudinary, is_cloudinary_configured

bp = Blueprint('uploads', __name__)

_ALLOWED_EXTENSIONS = {
    # Images
    'png', 'jpg', 'jpeg', 'gif', 'webp',
    # Audio
    'webm', 'ogg', 'mp4', 'm4a', 'wav', 'opus',
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB hard limit for this endpoint


@bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """
    Generic file upload endpoint.

    Accepts:  multipart/form-data  with field 'file'
    Returns:  { "url": "https://res.cloudinary.com/...", "resource_type": "..." }
    """
    if not is_cloudinary_configured():
        return jsonify({'error': 'Media storage is not configured on this server'}), 503

    uploaded = request.files.get('file')
    if not uploaded or not uploaded.filename:
        return jsonify({'error': 'No file provided. Send the file in the "file" form field.'}), 400

    ext = uploaded.filename.rsplit('.', 1)[-1].lower() if '.' in uploaded.filename else ''
    if ext not in _ALLOWED_EXTENSIONS:
        return jsonify({
            'error': f'Unsupported file type ".{ext}". '
                     f'Allowed: {", ".join(sorted(_ALLOWED_EXTENSIONS))}'
        }), 400

    # Check size before streaming to Cloudinary
    uploaded.stream.seek(0, 2)  # seek to end
    file_size = uploaded.stream.tell()
    uploaded.stream.seek(0)
    if file_size > MAX_UPLOAD_BYTES:
        return jsonify({'error': f'File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024*1024)} MB'}), 413

    secure_url, upload_err = upload_to_cloudinary(
        uploaded.stream,
        folder='pulse/uploads',
        public_id=uuid.uuid4().hex,
    )
    if upload_err:
        return jsonify({'error': upload_err}), 500

    return jsonify({'url': secure_url}), 200
