from typing import Any, Dict, List, Type, TypeVar

from app.exceptions.base import ServiceException


from app.exceptions.exception_handlers import handle_service_error
from app.utils.logger_helper import handle_log

from app.models import Post, Comment

T = TypeVar("T", bound=Post | Comment)


def create_model_list(input_data: List[Dict[str, Any]], model: Type[T]) -> List[T]:
    """
    Instantiate Post or Comment objects from raw data.
    """
    try:
        handle_log(
            "Creating list of model instances",
            event_key="CREATING_MODELS",
            log_level="info",
            service_method="create_model_list",
            model=model.__name__,
        )
        items = [model(d) for d in input_data]

    except (TypeError, ValueError) as e:
        handle_service_error(
            e,
            f"Internal Server Error: Failed to create {model.__name__} instances.",
            f"Error creating {model.__name__} instances",
            exc_type=ServiceException,
            service_method="create_model_list",
            model=model.__name__,
            method="create_model_list",
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
