"""
Routes package initialization.
"""
from app.routes.user_routes import user_bp
from app.routes.feed_routes import feed_bp

__all__ = ['user_bp', 'feed_bp']
