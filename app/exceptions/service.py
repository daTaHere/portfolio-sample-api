"""This module defines custom exceptions for service layer errors."""

from typing import Optional

from app.exceptions.base import ServiceExceptionV2


class ServiceInternalException(ServiceExceptionV2):
    """Exception to handle internal errors in services."""

    def __init__(
        self,
        message: str = "Internal Error: failed to process service data incorrect type/value or attribute",
        model: Optional[str] = None,
        **kwargs
    ):

        self.model = model
        super().__init__(message=message, **kwargs)


class ServiceValidationException(ServiceExceptionV2):
    """Exception to handle data validation errors in services."""

    def __init__(
        self,
        message: str = "Validation Error: invalid data failed (de)serialization",
        schema: Optional[str] = None,
        **kwargs
    ):

        self.schema = schema
        super().__init__(message=message, **kwargs)
