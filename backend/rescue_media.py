#!/usr/bin/env python3
"""
rescue_media.py
===============
Rescues media that is still being served by the live Railway app BEFORE
you redeploy (which would wipe Railway's ephemeral filesystem).

How it works:
  1. Connects to your Railway MySQL and finds all local media references
  2. Downloads each file from your live Railway app URL (e.g. https://yourapp.railway.app/uploads/...)
  3. Uploads each file to Cloudinary
  4. Updates the MySQL record with the new Cloudinary URL

Run this locally BEFORE pushing/deploying the Cloudinary changes.

Usage
-----
    pip install cloudinary pymysql requests python-dotenv
    python rescue_media.py --app-url https://yourapp.railway.app --dry-run
    python rescue_media.py --app-url https://yourapp.railway.app

Required env vars (set in a .env.railway file or export them):
    RAILWAY_DB_HOST      — from Railway MySQL service → Variables
    RAILWAY_DB_PORT      — usually 3306
    RAILWAY_DB_NAME
    RAILWAY_DB_USER
    RAILWAY_DB_PASSWORD
    CLOUDINARY_CLOUD_NAME
    CLOUDINARY_API_KEY
    CLOUDINARY_API_SECRET
"""

import argparse
import os
import re
import sys
import tempfile

import cloudinary
import cloudinary.uploader
import pymysql
import requests
from dotenv import load_dotenv

# Load .env.railway if it exists, else fall back to .env
load_dotenv('.env.railway', override=True)
load_dotenv('.env', override=False)

# ── Cloudinary ────────────────────────────────────────────────────────────────
cloudinary.config(
    cloud_name=os.environ['CLOUDINARY_CLOUD_NAME'],
    api_key=os.environ['CLOUDINARY_API_KEY'],
    api_secret=os.environ['CLOUDINARY_API_SECRET'],
    secure=True,
)

# ── Railway MySQL ─────────────────────────────────────────────────────────────
DB_HOST     = os.environ['MYSQLHOST']
DB_PORT     = int(os.getenv('MYSQLPORT', 3306))
DB_NAME     = os.environ['MYSQLDATABASE']
DB_USER     = os.environ['MYSQLUSER']
DB_PASSWORD = os.environ['MYSQLPASSWORD']


def db_connect():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, db=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )


def download_file(url: str) -> bytes:
    """Download a URL and return its raw bytes. Raises on HTTP error."""
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def upload_bytes_to_cloudinary(data: bytes, filename: str, folder: str) -> str:
    """Write bytes to a temp file and upload to Cloudinary. Returns secure_url."""
    suffix = os.path.splitext(filename)[-1] or '.bin'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        result = cloudinary.uploader.upload(
            tmp_path,
            folder=folder,
            resource_type='auto',
            overwrite=False,
        )
        return result['secure_url']
    finally:
        os.unlink(tmp_path)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Rescue post media  (media table)
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_media_url_column(conn):
    """Add media_url column if it doesn't exist yet (runs before new code is deployed)."""
    with conn.cursor() as cur:
        try:
            cur.execute("ALTER TABLE media ADD COLUMN media_url VARCHAR(500) NULL")
            conn.commit()
            print("  [INFO] Added media_url column to media table")
        except Exception:
            pass  # column already exists — safe to ignore


def rescue_post_media(conn, app_url: str, dry_run: bool):
    print("\n── Post media (media table) ──────────────────────────────────────")
    _ensure_media_url_column(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT id, file_path, media_url FROM media WHERE media_url IS NULL")
        rows = cur.fetchall()
    print(f"  {len(rows)} rows need migration")

    ok = skip = fail = 0
    for row in rows:
        media_id  = row['id']
        file_path = row['file_path']   # e.g. "/abs/path/uploads/abc.jpg"  or  "uploads/abc.jpg"

        # Extract just the filename portion after /uploads/
        m = re.search(r'/uploads/(.+)$', file_path.replace('\\', '/'))
        if not m:
            print(f"  [SKIP] media id={media_id}  can't parse path: {file_path}")
            skip += 1
            continue

        rel_path   = m.group(1)   # e.g. "abc123.jpg" or "profiles/pic.jpg"
        file_url   = f"{app_url.rstrip('/')}/uploads/{rel_path}"
        filename   = os.path.basename(rel_path)

        if dry_run:
            print(f"  [DRY]  media id={media_id}  {file_url}")
            ok += 1
            continue

        try:
            data       = download_file(file_url)
            cloud_url  = upload_bytes_to_cloudinary(data, filename, folder='pulse/posts')
            with conn.cursor() as cur:
                cur.execute("UPDATE media SET media_url = %s WHERE id = %s", (cloud_url, media_id))
            conn.commit()
            print(f"  [OK]   media id={media_id}  → {cloud_url}")
            ok += 1
        except requests.HTTPError as exc:
            print(f"  [SKIP] media id={media_id}  HTTP {exc.response.status_code} for {file_url}")
            skip += 1
        except Exception as exc:
            print(f"  [FAIL] media id={media_id}  {exc}")
            fail += 1

    print(f"  Done: {ok} uploaded, {skip} skipped, {fail} failed")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Rescue message audio/images  (messages.content field)
# ─────────────────────────────────────────────────────────────────────────────

_AUDIO_RE = re.compile(r'^\[audio\](/api/uploads/.+)$')
_IMAGE_RE = re.compile(r'^\[image\](/api/uploads/.+)$')


def rescue_messages(conn, app_url: str, dry_run: bool):
    print("\n── Message audio + images ────────────────────────────────────────")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, content FROM messages "
            "WHERE content LIKE '[audio]/api/uploads/%' "
            "   OR content LIKE '[image]/api/uploads/%'"
        )
        rows = cur.fetchall()
    print(f"  {len(rows)} messages need migration")

    ok = skip = fail = 0
    for row in rows:
        msg_id  = row['id']
        content = row['content']

        audio_m = _AUDIO_RE.match(content)
        image_m = _IMAGE_RE.match(content)

        if audio_m:
            api_path  = audio_m.group(1)   # /api/uploads/filename.webm
            prefix    = '[audio]'
            folder    = 'pulse/messages/audio'
        elif image_m:
            api_path  = image_m.group(1)   # /api/uploads/filename.jpg
            prefix    = '[image]'
            folder    = 'pulse/messages/images'
        else:
            skip += 1
            continue

        # Convert /api/uploads/file.ext → /uploads/file.ext  (Flask serves at /uploads/)
        uploads_path = api_path.replace('/api/uploads/', '/uploads/', 1)
        file_url     = f"{app_url.rstrip('/')}{uploads_path}"
        filename     = os.path.basename(uploads_path)

        if dry_run:
            print(f"  [DRY]  message id={msg_id}  {file_url}")
            ok += 1
            continue

        try:
            data      = download_file(file_url)
            cloud_url = upload_bytes_to_cloudinary(data, filename, folder=folder)
            new_content = f"{prefix}{cloud_url}"
            with conn.cursor() as cur:
                cur.execute("UPDATE messages SET content = %s WHERE id = %s", (new_content, msg_id))
            conn.commit()
            print(f"  [OK]   message id={msg_id}  → {cloud_url}")
            ok += 1
        except requests.HTTPError as exc:
            print(f"  [SKIP] message id={msg_id}  HTTP {exc.response.status_code} for {file_url}")
            skip += 1
        except Exception as exc:
            print(f"  [FAIL] message id={msg_id}  {exc}")
            fail += 1

    print(f"  Done: {ok} uploaded, {skip} skipped, {fail} failed")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Rescue profile pictures + headers  (users table)
# ─────────────────────────────────────────────────────────────────────────────

def rescue_users(conn, app_url: str, dry_run: bool):
    print("\n── User profile pictures + headers ──────────────────────────────")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, profile_picture, header_image FROM users "
            "WHERE (profile_picture IS NOT NULL AND profile_picture NOT LIKE 'http%') "
            "   OR (header_image    IS NOT NULL AND header_image    NOT LIKE 'http%')"
        )
        rows = cur.fetchall()
    print(f"  {len(rows)} users with local image paths")

    ok = skip = fail = 0
    for row in rows:
        user_id = row['id']
        updates = {}

        for field, folder in (
            ('profile_picture', 'pulse/profiles'),
            ('header_image',    'pulse/headers'),
        ):
            value = row[field]
            if not value or value.startswith('http'):
                continue

            # value is like  "profiles/profile_3_abc.jpg"  or  "headers/header_3_xyz.jpg"
            file_url = f"{app_url.rstrip('/')}/uploads/{value.lstrip('/')}"
            filename = os.path.basename(value)

            if dry_run:
                print(f"  [DRY]  user id={user_id} {field}  {file_url}")
                ok += 1
                continue

            try:
                data      = download_file(file_url)
                cloud_url = upload_bytes_to_cloudinary(data, filename, folder=folder)
                updates[field] = cloud_url
                print(f"  [OK]   user id={user_id} {field}  → {cloud_url}")
                ok += 1
            except requests.HTTPError as exc:
                print(f"  [SKIP] user id={user_id} {field}  HTTP {exc.response.status_code}")
                skip += 1
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

    print(f"  Done: {ok} uploaded, {skip} skipped, {fail} failed")


# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Rescue Railway media → Cloudinary')
    parser.add_argument('--app-url', required=True,
                        help='Base URL of your live Railway app, e.g. https://yourapp.railway.app')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be migrated without uploading anything')
    args = parser.parse_args()

    if args.dry_run:
        print("DRY-RUN — no uploads, no DB writes")

    print(f"\nApp URL    : {args.app_url}")
    print(f"Database   : {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Cloudinary : {cloudinary.config().cloud_name}")

    try:
        conn = db_connect()
    except Exception as exc:
        print(f"\nFailed to connect to MySQL: {exc}")
        sys.exit(1)

    try:
        rescue_post_media(conn, args.app_url, args.dry_run)
        rescue_messages(conn,   args.app_url, args.dry_run)
        rescue_users(conn,      args.app_url, args.dry_run)
    finally:
        conn.close()

    print("\nRescue complete. You can now redeploy safely.")


if __name__ == '__main__':
    main()
