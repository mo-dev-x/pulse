#!/usr/bin/env python3
"""
migrate_to_cloudinary.py
========================
One-shot script that:
  1. Reads every local media file referenced in the database
  2. Uploads it to Cloudinary
  3. Updates the MySQL record with the new Cloudinary URL

Run ONCE after deploying the Cloudinary integration.
Safe to re-run: rows whose media_url is already set are skipped.

Usage
-----
    cd backend
    pip install cloudinary python-dotenv pymysql
    python migrate_to_cloudinary.py

    # Dry-run (no DB writes, no uploads):
    python migrate_to_cloudinary.py --dry-run

Environment variables required (loaded from .env automatically):
    CLOUDINARY_CLOUD_NAME
    CLOUDINARY_API_KEY
    CLOUDINARY_API_SECRET
    MYSQLHOST / DB_HOST
    MYSQLPORT / DB_PORT
    MYSQLDATABASE / DB_NAME
    MYSQLUSER / DB_USER
    MYSQLPASSWORD / DB_PASSWORD
    UPLOAD_FOLDER  (optional; defaults to ./uploads)
"""

import argparse
import os
import sys
import re

import cloudinary
import cloudinary.uploader
import pymysql
from dotenv import load_dotenv

load_dotenv()

# ── Cloudinary config ────────────────────────────────────────────────────────
cloudinary.config(
    cloud_name=os.environ['CLOUDINARY_CLOUD_NAME'],
    api_key=os.environ['CLOUDINARY_API_KEY'],
    api_secret=os.environ['CLOUDINARY_API_SECRET'],
    secure=True,
)

# ── DB config ─────────────────────────────────────────────────────────────────
DB_HOST = os.getenv('MYSQLHOST', os.getenv('DB_HOST', 'localhost'))
DB_PORT = int(os.getenv('MYSQLPORT', os.getenv('DB_PORT', 3306)))
DB_NAME = os.getenv('MYSQLDATABASE', os.getenv('DB_NAME', 'pulse_db'))
DB_USER = os.getenv('MYSQLUSER', os.getenv('DB_USER', 'root'))
DB_PASSWORD = os.getenv('MYSQLPASSWORD', os.getenv('DB_PASSWORD', ''))

UPLOAD_ROOT = os.path.abspath(os.getenv('UPLOAD_FOLDER', './uploads'))


def get_connection():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, db=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )


def upload_file(local_path: str, folder: str) -> str:
    """Upload a local file to Cloudinary and return its secure_url."""
    result = cloudinary.uploader.upload(
        local_path,
        folder=folder,
        resource_type='auto',
        overwrite=False,
    )
    return result['secure_url']


# ─────────────────────────────────────────────────────────────────────────────
# 1. Migrate post media (media table)
# ─────────────────────────────────────────────────────────────────────────────

def migrate_post_media(conn, dry_run: bool):
    print("\n── Post media (media table) ──────────────────────────────────────")
    with conn.cursor() as cur:
        cur.execute("SELECT id, file_path, media_url FROM media WHERE media_url IS NULL")
        rows = cur.fetchall()
    print(f"  Found {len(rows)} rows without a Cloudinary URL")

    ok = skip = fail = 0
    for row in rows:
        media_id = row['id']
        raw_path = row['file_path']

        # Build the absolute local path
        # file_path may be stored as 'uploads/abc.jpg' or an absolute path
        if os.path.isabs(raw_path):
            local_path = raw_path
        else:
            # strip leading 'uploads/' prefix that some rows carry
            rel = re.sub(r'^uploads[/\\]', '', raw_path)
            local_path = os.path.join(UPLOAD_ROOT, rel)

        if not os.path.isfile(local_path):
            print(f"  [SKIP] media id={media_id}  file not found: {local_path}")
            skip += 1
            continue

        if dry_run:
            print(f"  [DRY]  media id={media_id}  would upload: {local_path}")
            ok += 1
            continue

        try:
            url = upload_file(local_path, folder='pulse/posts')
            with conn.cursor() as cur:
                cur.execute("UPDATE media SET media_url = %s WHERE id = %s", (url, media_id))
            conn.commit()
            print(f"  [OK]   media id={media_id}  → {url}")
            ok += 1
        except Exception as exc:
            print(f"  [FAIL] media id={media_id}  {exc}")
            fail += 1

    print(f"  Done: {ok} uploaded, {skip} skipped (missing), {fail} failed")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Migrate message media (messages table — content field)
# ─────────────────────────────────────────────────────────────────────────────

_MSG_AUDIO_RE = re.compile(r'^\[audio\]/api/uploads/(.+)$')
_MSG_IMAGE_RE = re.compile(r'^\[image\]/api/uploads/(.+)$')


def migrate_messages(conn, dry_run: bool):
    print("\n── Messages (audio + image) ──────────────────────────────────────")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, content FROM messages "
            "WHERE content LIKE '[audio]/api/uploads/%' "
            "   OR content LIKE '[image]/api/uploads/%'"
        )
        rows = cur.fetchall()
    print(f"  Found {len(rows)} media messages to migrate")

    ok = skip = fail = 0
    for row in rows:
        msg_id = row['id']
        content = row['content']

        audio_m = _MSG_AUDIO_RE.match(content)
        image_m = _MSG_IMAGE_RE.match(content)

        if audio_m:
            filename = audio_m.group(1)
            prefix = '[audio]'
            folder = 'pulse/messages/audio'
        elif image_m:
            filename = image_m.group(1)
            prefix = '[image]'
            folder = 'pulse/messages/images'
        else:
            skip += 1
            continue

        local_path = os.path.join(UPLOAD_ROOT, filename)
        if not os.path.isfile(local_path):
            print(f"  [SKIP] message id={msg_id}  file not found: {local_path}")
            skip += 1
            continue

        if dry_run:
            print(f"  [DRY]  message id={msg_id}  would upload: {local_path}")
            ok += 1
            continue

        try:
            url = upload_file(local_path, folder=folder)
            new_content = f"{prefix}{url}"
            with conn.cursor() as cur:
                cur.execute("UPDATE messages SET content = %s WHERE id = %s", (new_content, msg_id))
            conn.commit()
            print(f"  [OK]   message id={msg_id}  → {url}")
            ok += 1
        except Exception as exc:
            print(f"  [FAIL] message id={msg_id}  {exc}")
            fail += 1

    print(f"  Done: {ok} uploaded, {skip} skipped (missing), {fail} failed")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Migrate user profile pictures and headers
# ─────────────────────────────────────────────────────────────────────────────

def migrate_users(conn, dry_run: bool):
    print("\n── User profile pictures and headers ────────────────────────────")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, profile_picture, header_image FROM users "
            "WHERE (profile_picture IS NOT NULL AND profile_picture NOT LIKE 'http%') "
            "   OR (header_image IS NOT NULL AND header_image NOT LIKE 'http%')"
        )
        rows = cur.fetchall()
    print(f"  Found {len(rows)} users with local image paths")

    ok = skip = fail = 0
    for row in rows:
        user_id = row['id']
        updates = {}

        for field, folder in (
            ('profile_picture', 'pulse/profiles'),
            ('header_image', 'pulse/headers'),
        ):
            value = row[field]
            if not value or value.startswith('http'):
                continue

            local_path = os.path.join(UPLOAD_ROOT, value)
            if not os.path.isfile(local_path):
                print(f"  [SKIP] user id={user_id} {field}  file not found: {local_path}")
                skip += 1
                continue

            if dry_run:
                print(f"  [DRY]  user id={user_id} {field}  would upload: {local_path}")
                ok += 1
                continue

            try:
                url = upload_file(local_path, folder=folder)
                updates[field] = url
                print(f"  [OK]   user id={user_id} {field}  → {url}")
                ok += 1
            except Exception as exc:
                print(f"  [FAIL] user id={user_id} {field}  {exc}")
                fail += 1

        if updates and not dry_run:
            set_clause = ', '.join(f"{k} = %s" for k in updates)
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE users SET {set_clause} WHERE id = %s",
                    (*updates.values(), user_id),
                )
            conn.commit()

    print(f"  Done: {ok} uploaded, {skip} skipped (missing), {fail} failed")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Migrate local media to Cloudinary')
    parser.add_argument('--dry-run', action='store_true', help='Preview only — no uploads or DB writes')
    args = parser.parse_args()

    if args.dry_run:
        print("DRY-RUN MODE — no files will be uploaded and no DB rows will be updated")

    print(f"\nUpload root : {UPLOAD_ROOT}")
    print(f"Database    : {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Cloudinary  : {cloudinary.config().cloud_name}")

    try:
        conn = get_connection()
    except Exception as exc:
        print(f"\nFailed to connect to MySQL: {exc}")
        sys.exit(1)

    try:
        migrate_post_media(conn, dry_run=args.dry_run)
        migrate_messages(conn, dry_run=args.dry_run)
        migrate_users(conn, dry_run=args.dry_run)
    finally:
        conn.close()

    print("\nMigration complete.")


if __name__ == '__main__':
    main()
