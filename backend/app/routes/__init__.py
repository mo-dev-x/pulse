"""
Routes package

Contains all API endpoint blueprints.
"""

from app.routes import auth, posts, social, reactions, analytics, comments

__all__ = ['auth', 'posts', 'social', 'reactions', 'analytics', 'comments']
