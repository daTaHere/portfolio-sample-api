"""Functions related to building feed models from raw data."""

from typing import Any, Dict, List, Type, TypeVar

from app.models import Post, Comment

from app.exceptions.service import ServiceInternalException, ServiceValidationException
from app.exceptions.exception_handlers import handle_service_errorV2
from app.utils.logger_helper import handle_log


T = TypeVar("T", bound=Post | Comment)


def create_model_list(input_data: List[Dict[str, Any]], model: Type[T]) -> List[T]:
    """
    Instantiate Post or Comment objects from raw data and return a list of model instances.
    """

    items: List[T] = []

    try:
        handle_log(
            "Creating list of model instances",
            event_key="CREATING_MODELS",
            log_level="info",
            service_method="create_model_list",
            model=model.__name__,
        )
        items = [model(data) for data in input_data]

    except (KeyError, TypeError, ValueError) as e:
        handle_service_errorV2(
            e,
            f"Error creating {model.__name__} instances",
            exc_type=ServiceValidationException,
            service_method="create_model_list",
        )
    except AttributeError as e:
        handle_service_errorV2(
            e,
            f"Attribute error creating {model.__name__} instances",
            exc_type=ServiceInternalException,
            service_method="create_model_list",
            model=model.__name__,
        )

    handle_log(
        "Success List of model instances created",
        event_key="SUCCESS",
        log_level="info",
        service_method="create_model_list",
        model=model.__name__,
        items=len(items),
    )

    return items
