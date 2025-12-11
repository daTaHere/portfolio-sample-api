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

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # CORS settings
    CORS_HEADERS = "Content-Type"

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

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

    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = os.getenv("REDIS_PORT", 6379)
    REDIS_DB = os.getenv("REDIS_DB", 0)

    # Request timeout settings
    REQUEST_TIMEOUT = 10  # seconds


class DevelopmentConfig(Config):
    """Development environment configuration."""

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

    DEBUG = False
    TESTING = False

    # PostgreSQL for staging
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://placeholder_user:placeholder_password@localhost:5432/placeholder_staging_db",
    )


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False

    # PostgreSQL for production
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://placeholder_user:placeholder_password@localhost:5432/placeholder_production_db",
    )

    # Enhanced security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = True
    TESTING = True

    # In-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
