"""
User data model.
Defines the User table schema.
"""

from app import db
from datetime import datetime


class User(db.Model):
    """User model for storing user information."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.id}: {self.name}>"

    # This method will be replaced with marshmallow schema for serialization
    def to_dict(self):
        """Convert User object to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
