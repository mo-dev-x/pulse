"""Task helpers for running jobs with an application context."""

import os
from contextlib import contextmanager

from flask import current_app, has_app_context


@contextmanager
def task_app_context():
    """Provide an app context for worker execution or eager calls."""
    if has_app_context():
        yield current_app._get_current_object()
        return

    from app import create_app

    config_name = os.getenv('FLASK_CONFIG', 'development')
    app = create_app(config_name)
    with app.app_context():
        yield app
