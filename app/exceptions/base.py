"""This module defines base exception classes for the application."""

from typing import Optional


class APIException(Exception):
    """Base exception for external API errors."""

    def __init__(
        self,
        message: str,
        endpoint: str,
        method: str,
        original_exception: Exception = None,
    ):
        self.endpoint = endpoint
        self.method = method
        self.original_exception = original_exception
        super().__init__(message)


class APIExceptionV2(Exception):
    """Base exception for external API errors."""

    def __init__(
        self,
        message: str = "External API error occurred",
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
    ):
        self.endpoint = endpoint
        self.method = method

        super().__init__(message)


class ServiceException(Exception):
    """Base exception for service / business logic errors."""

    def __init__(
        self,
        message: str,
        endpoint: str,
        method: str,
        model: str = None,
        key: str = None,
        # original_exception: Exception = None,
    ):
        self.endpoint = endpoint
        self.model = model
        self.method = method
        self.key = key
        # self.original_exception = original_exception
        super().__init__(message)


class ServiceExceptionV2(Exception):
    """Base exception for service / business logic errors."""

    def __init__(
        self,
        message: str,
        service_method: str,
    ):
        self.service_method = service_method
        super().__init__(message)


class DatabaseException(Exception):
    """Base exception for database / storage errors."""

    def __init__(
        self,
        message: str,
        query: str = None,
        service_method: str = None,
        original_exception: Exception = None,
    ):
        self.query = query
        self.service_method = service_method
        self.original_exception = original_exception
        super().__init__(message)
