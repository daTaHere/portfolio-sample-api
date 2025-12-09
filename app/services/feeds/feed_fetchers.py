"""Functions related to fetching feed data from external APIs."""

import httpx
import asyncio

from typing import Any, Dict, List

from app.exceptions.base import (
    APIException,
    ServiceException,
)

from app.exceptions.exception_handlers import handle_service_error
from app.utils.logger_helper import handle_log
from app.schemas import PostSchema, CommentSchema

from marshmallow import ValidationError


POST_ENDPOINT = "posts"
MAX_RETRIES = 3
HTTP_TIMEOUT_SECONDS = 5.0
RETRY_BACKOFF_BASE = 0.2  # seconds
POST_SCHEMA = PostSchema(many=True)
COMMENT_SCHEMA = CommentSchema(many=True)


async def send_request(endpoint: str) -> List[Dict[str, Any]]:
    """
    Send HTTP request to 3rd party API and return JSON list.
    Handles network, HTTP status, and JSON decoding errors.
    """
    url = endpoint
    validator = POST_SCHEMA if POST_ENDPOINT in endpoint else COMMENT_SCHEMA
    data = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            handle_log(
                "Attempting request",
                method="GET",
                event_key="ATTEMPTS",
                log_level="info",
                service_method="send_request",
                request_attempt=attempt,
                endpoint=url,
            )
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
                res = await client.get(url)
                res.raise_for_status()

                try:
                    handle_log(
                        "Validating response data",
                        event_key="VALIDATION",
                        log_level="debug",
                        service_method="send_request",
                        endpoint=url,
                    )

                    # Validate and deserialize response data
                    data = validator.load(res.json())
                    break  # exit retry loop on success
                except httpx.DecodingError as e:
                    handle_service_error(
                        e,
                        "External API Error: Invalid JSON response.",
                        "Request returned invalid JSON.",
                        exc_type=APIException,
                        url=url,
                        service_method="send_request",
                    )
        except (httpx.RequestError, httpx.ConnectTimeout) as e:
            wait_time = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))

            if attempt == MAX_RETRIES:
                handle_service_error(
                    e,
                    "External API Error: Unreachable",
                    "Request failed. Exhausted all retries.",
                    exc_type=APIException,
                    url=url,
                    service_method="send_request",
                )
            handle_log(
                f"Request attempt failed, retrying in {wait_time:.2f}s",
                method="GET",
                event_key="RETRIES",
                log_level="warning",
                service_method="send_request",
                endpoint=url,
                request_attempt=attempt,
                error=str(e),
            )
            await asyncio.sleep(wait_time)
        except httpx.HTTPStatusError as e:
            handle_service_error(
                e,
                f"External API Error: Bad status code: {e.response.status_code}",
                "Request returned bad status code.",
                exc_type=APIException,
                url=url,
                service_method="send_request",
            )
        except ValidationError as e:
            handle_service_error(
                e,
                "External API Error: Data validation failed.",
                "Response data validation error.",
                exc_type=APIException,
                url=url,
                service_method="send_request",
            )
        except (TypeError, ValueError) as e:
            handle_service_error(
                e,
                "Internal Error: Type or value error.",
                "Response data type or value error.",
                event_key="ERROR",
                log_level="debug",
                exc_type=ServiceException,
                service_method="send_request",
                endpoint=url,
                error=str(e),
            )

    handle_log(
        "Successful response received",
        method="GET",
        event_key="SUCCESS",
        log_level="info",
        service_method="send_request",
        endpoint=url,
        items=len(data),
    )

    return data
