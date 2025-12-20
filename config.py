"""
Configuration settings for Flask application.
Supports multiple environments: development, staging, production.
"""

import os
from pathlib import Path


class Config:
    """Base configuration with defaults."""

    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Redis settings
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REQUEST_TIMEOUT = 10  # seconds
    REDIS_SOCKET_CONNECT_TIMEOUT = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", 0.2))
    REDIS_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", 0.8))

    # Celery settings
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # External API settings
    OPENWEATHER_API_KEY = os.getenv(
        "OPENWEATHER_API_KEY", "placeholder-openweather-api-key"
    )
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    JSONPLACEHOLDER_BASE_URL = "https://jsonplaceholder.typicode.com"

    # CORS settings
    CORS_HEADERS = "Content-Type"


class DevelopmentConfig(Config):
    """Development environment configuration."""

    # Flask settings
    DEBUG = True
    TESTING = False

    # SQLite database for local development
    BASE_DIR = Path(__file__).resolve().parent
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f'sqlite:///{BASE_DIR / "instance" / "dev.db"}'
    )
    SQLALCHEMY_ECHO = True


class StagingConfig(Config):
    """Staging environment configuration."""

    # Flask settings
    DEBUG = False
    TESTING = False

    # Database settings (Postgres)
    # Note: Update connection string in production using environment variable
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://placeholder_user:placeholder_password@localhost:5432/placeholder_staging_db",
    )


class ProductionConfig(Config):
    """Production environment configuration."""

    # Flask settings
    DEBUG = False
    TESTING = False

    # Enhanced security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600

    # Database settings (Postgres)
    # Note: Update connection string in production using environment variable
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://placeholder_user:placeholder_password@localhost:5432/placeholder_production_db",
    )


class TestingConfig(Config):
    """Testing environment configuration."""

    # Flask settings
    DEBUG = True
    TESTING = True

    # Database settings (In-memory SQLite)
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
