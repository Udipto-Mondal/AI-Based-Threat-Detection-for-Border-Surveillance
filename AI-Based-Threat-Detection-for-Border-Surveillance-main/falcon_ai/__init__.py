"""
Falcon AI package initializer.
Exposes the Flask application factory for convenience.
"""
from .app import create_app, mongo, login_manager, bcrypt  # noqa: F401

