"""
Flask application factory.
Initializes and configures the Flask app with all extensions.
"""

import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.middleware.proxy_fix import ProxyFix

from app.logging import logger
from app.clients.redis_client import init_redis


# Initialize extensions
db = SQLAlchemy()


def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app instances.

    Args:
        config_name (str): Configuration name (development, staging, production, testing)

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    from config import config

    app.config.from_object(config.get(config_name, config["default"]))

    # Initialize extensions
    db.init_app(app)
    init_redis(app)
    CORS(app)

    # --- Production ProxyFix config (trust first proxy) ---

    # 🔒 Trust exactly 1 proxy hop
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1,
    )

    # Register blueprints
    from app.routes import user_bp, feed_bp, weather_bp

    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(feed_bp, url_prefix="/api")
    app.register_blueprint(weather_bp, url_prefix="/api")

    # --- initialize scheduler ---
    from app.tasks import fetch_weather_updates

    scheduler = BackgroundScheduler()
    # Add jobs here, e.g.:
    scheduler.add_job(func=fetch_weather_updates, trigger="interval", minutes=52)
    scheduler.start()

    # Create database tables
    with app.app_context():
        db.create_all()

    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint for monitoring."""
        return {"status": "healthy", "service": "portfolio-sample-api"}, 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        logger.warning("not_found", path=error.description)
        return {"error": "Resource not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error("internal_server_error", error=str(error))
        db.session.rollback()
        return {"error": "Internal server error"}, 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions."""
        logger.error("unhandled_exception", error=str(error), type=type(error).__name__)
        db.session.rollback()
        return {"error": "An unexpected error occurred"}, 500

    logger.info("flask_app_created", config=config_name)

    return app
