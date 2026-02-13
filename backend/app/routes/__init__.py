"""
Routes package

Contains all API endpoint blueprints.
"""

from app.routes import auth, posts 

# We'll add other blueprints as we create them:
# from app.routes import users
# from app.routes import analytics
# from app.routes import reactions

__all__ = ['auth', 'posts']