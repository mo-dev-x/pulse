"""Seed Meilisearch indexes from the current database."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models import CampusZone, Post, User
from app.services import upsert_documents


def _post_doc(post):
    return {
        'id': post.id,
        'content': post.content,
        'is_anonymous': post.is_anonymous,
        'hidden_by_mod': post.hidden_by_mod,
        'zone_id': post.zone_id,
        'zone_name': post.zone.name if post.zone else None,
        'author_display_name': post.author.display_name if post.author else None,
        'author_is_deactivated': bool(post.author.is_deactivated) if post.author else False,
        'created_at': post.created_at.isoformat() if post.created_at else None,
    }


def _user_doc(user):
    return {
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name,
        'bio': user.bio,
        'profile_picture': user.profile_picture,
        'profile_visibility': user.profile_visibility,
        'is_deactivated': bool(user.is_deactivated),
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }


def _zone_doc(zone):
    return {
        'id': zone.id,
        'name': zone.name,
        'description': zone.description,
        'zone_type': zone.zone_type,
    }


def main():
    app = create_app('development')
    with app.app_context():
        posts = [_post_doc(post) for post in Post.query.all()]
        users = [_user_doc(user) for user in User.query.all()]
        zones = [_zone_doc(zone) for zone in CampusZone.query.all()]

        print(f'Preparing posts index: {len(posts)} documents')
        upsert_documents('posts', posts)
        print(f'Pushed posts index: {len(posts)} documents')

        print(f'Preparing users index: {len(users)} documents')
        upsert_documents('users', users)
        print(f'Pushed users index: {len(users)} documents')

        print(f'Preparing zones index: {len(zones)} documents')
        upsert_documents('zones', zones)
        print(f'Pushed zones index: {len(zones)} documents')

        print(f'Reindexed posts={len(posts)} users={len(users)} zones={len(zones)}')


if __name__ == '__main__':
    main()
