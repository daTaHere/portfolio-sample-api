"""
User service layer.
Business logic for user operations.
"""

from app import db
from app.logging import logger
from app.models.user_model import User
from typing import List, Optional


def get_all_users() -> List[dict]:
    """
    Query the database for all users.

    Returns:
        List[dict]: Array of user objects as dictionaries
    """
    try:
        users = User.query.all()
        logger.info("get_all_users", count=len(users))
        return [user.to_dict() for user in users]
    except Exception as e:
        logger.error("get_all_users_error", error=str(e))
        raise


def create_user(name: str) -> int:
    """
    Insert a new user into the User table.

    Args:
        name (str): The name of the user to create

    Returns:
        int: The ID of the newly created user

    Raises:
        ValueError: If name is empty or invalid
        Exception: If database operation fails
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")

    try:
        user = User(name=name.strip())
        db.session.add(user)
        db.session.commit()

        logger.info("user_created", user_id=user.id, name=user.name)
        return user.id
    except Exception as e:
        db.session.rollback()
        logger.error("create_user_error", error=str(e), name=name)
        raise


def get_user_by_id(user_id: int) -> Optional[dict]:
    """
    Get a user by ID.

    Args:
        user_id (int): The ID of the user to retrieve

    Returns:
        Optional[dict]: User object as dictionary or None if not found
    """
    try:
        user = User.query.get(user_id)
        if user:
            logger.info("get_user_by_id", user_id=user_id, found=True)
            return user.to_dict()
        logger.info("get_user_by_id", user_id=user_id, found=False)
        return None
    except Exception as e:
        logger.error("get_user_by_id_error", error=str(e), user_id=user_id)
        raise
