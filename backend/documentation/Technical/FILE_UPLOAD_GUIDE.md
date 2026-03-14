# File Upload Guide

## Purpose
Document how Pulse handles profile and header image uploads, including storage paths, validation, and optimization behavior.

## Supported Upload Endpoints
- `POST /api/auth/upload-profile-pic`
- `POST /api/auth/upload-header`

## Storage Layout

```text
UPLOAD_FOLDER/
  profiles/
  headers/
```

Default configuration:
- `UPLOAD_FOLDER=uploads/`
- `PROFILE_UPLOAD_FOLDER=uploads/profiles`
- `HEADER_UPLOAD_FOLDER=uploads/headers`

## Validation Rules
- Allowed extensions:
  - `png`
  - `jpg`
  - `jpeg`
  - `gif`
  - `webp`
- Max request size:
  - `MAX_CONTENT_LENGTH=5242880` (5 MB default)
- Missing file:
  - returns `400`
- Invalid extension:
  - returns `400`
- Oversized upload:
  - Flask returns `413`

## Processing Behavior
### Profile Picture
- Target max size: `500x500`
- Saved as `.jpg`

### Header Image
- Target max size: `1500x500`
- Saved as `.jpg`

### Pillow Behavior
- If `Pillow` is installed:
  - Image is converted to RGB
  - Image is resized with thumbnail constraints
  - Optimized JPEG is written
- If `Pillow` is not installed:
  - Pulse falls back to direct file save
  - Upload still works, but optimization is skipped

## Environment Variables

```env
UPLOAD_FOLDER=/var/www/pulse/uploads
PROFILE_UPLOAD_FOLDER=/var/www/pulse/uploads/profiles
HEADER_UPLOAD_FOLDER=/var/www/pulse/uploads/headers
MAX_CONTENT_LENGTH=5242880
```

## Deployment Checklist
1. Create upload directories.
2. Ensure backend process has write permission.
3. Install `Pillow` in the active virtualenv for optimized resizing.
4. Back up uploaded assets.
5. Serve `/uploads/...` through the app or reverse proxy.

## Security Notes
- Restrict allowed file extensions.
- Do not trust original filenames.
- Keep uploads outside static source directories when possible.
- Consider virus scanning and object storage if upload scope expands beyond profile images.

## Verification
1. Upload a valid PNG profile picture.
2. Confirm API returns `200`.
3. Confirm file is written under `profiles/` or `headers/`.
4. When Pillow is installed, verify image dimensions were reduced as expected.
