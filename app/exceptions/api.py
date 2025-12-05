# app/exceptions/service_exceptions.py


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
