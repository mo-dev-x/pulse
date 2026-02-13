"""
Routes package

Contains all API endpoint blueprints.
"""

from app.routes import auth, posts, social, reactions, analytics

__all__ = ['auth', 'posts', 'social', 'reactions', 'analytics']