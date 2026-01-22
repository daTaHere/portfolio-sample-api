"""This module defines custom exceptions for transport layer errors."""

from app.exceptions.base import APIExceptionV2


class APIBadStatusCode(APIExceptionV2):
    """Exception to handle a bad response code from client."""

    def __init__(
        self,
        message: str = "Failed to fetch data: Bad status code from external API",
        service_name: str = None,
        **kwargs
    ):

        self.service_name = service_name
        super().__init__(message=message, **kwargs)


class APITimeoutException(APIExceptionV2):
    """Exception to handle timeout exception from client."""

    def __init__(
        self,
        message: str = "Unreachable resource: Host connection retries exhausted",
        service_name: str = None,
        **kwargs
    ):

        self.service_name = service_name
        super().__init__(message=message, **kwargs)


class APIConnectionException(APIExceptionV2):
    """Exception to handle failure to connect to external API."""

    def __init__(
        self,
        message: str = "Unreachable resource: Host Connection cannot be established",
        service_name: str = None,
        **kwargs
    ):

        self.service_name = service_name
        super().__init__(message=message, **kwargs)


class APIJSONDecodeException(APIExceptionV2):
    """Exception to handle JSON decode errors from external API."""

    def __init__(
        self,
        message: str = "JSONDecode Error: Received bad response from external API",
        service_name: str = None,
        **kwargs
    ):

        self.service_name = service_name
        super().__init__(message=message, **kwargs)


class APIValidationException(APIExceptionV2):
    """Exception to handle response validation errors from external API."""

    def __init__(
        self,
        message: str = "Validation Error: Received invalid data from external API",
        service_name: str = None,
        **kwargs
    ):

        self.service_name = service_name
        super().__init__(message=message, **kwargs)


class ExternalAPIConnectionError(Exception):
    """
    Raised when a service fails to reach an external API.
    Wraps the original low-level exception and preserves context.
    """

    def __init__(
        self,
        message: str,
        url: str = None,
        status_code: int = None,
        payload: dict = None,
    ):
        """
        Args:
            message: Human-readable error message.
            url: The endpoint URL that caused the failure (optional).
            status_code: HTTP status code if available (optional).
            payload: Request payload or relevant data (optional).
        """
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        self.payload = payload
