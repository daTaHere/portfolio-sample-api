# app/exceptions/base_exceptions.py


class APIException(Exception):
    """Base exception for external API errors."""

    def __init__(
        self,
        message: str,
        endpoint: str = None,
        method: str = None,
        original_exception: Exception = None,
    ):
        self.endpoint = endpoint
        self.method = method
        self.original_exception = original_exception
        super().__init__(message)


class ServiceException(Exception):
    """Base exception for service / business logic errors."""

    def __init__(
        self,
        message: str,
        service_method: str = None,
        model: str = None,
        key: str = None,
        original_exception: Exception = None,
    ):
        self.service_method = service_method
        self.model = model
        self.key = key
        self.original_exception = original_exception
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
