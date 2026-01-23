"""This module includes functions to fetch feed data from JSONPlaceholder API asynchronously."""

import asyncio
from json import JSONDecodeError
from typing import Any, Dict, List

import httpx
from marshmallow import ValidationError

from app.exceptions.api import (
    APIBadStatusCode,
    APIConnectionException,
    APIJSONDecodeException,
    APIValidationException,
    APITimeoutException,
)
from app.exceptions.service import ServiceInternalException
from app.exceptions.exception_handlers import handle_api_error, handle_service_errorV2
from app.utils.logger_helper import handle_log
from app.schemas import PostSchema, CommentSchema


POST_ENDPOINT = "https://jsonplaceholder.typicode.com/posts"
MAX_RETRIES = 3
HTTP_TIMEOUT_SECONDS = 5.0
RETRY_BACKOFF_BASE = 0.2  # seconds
POST_SCHEMA = PostSchema(many=True)
COMMENT_SCHEMA = CommentSchema(many=True)


async def send_request(endpoint: str) -> List[Dict[str, Any]]:
    """
    Fetch data from JSONPlaceholder API with retries, timeouts, and validation.
    Returns a list of posts or comments to build feeds.
    """
    url = endpoint
    validator = POST_SCHEMA if POST_ENDPOINT in endpoint else COMMENT_SCHEMA

    # Retry loop for handling transient errors
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            handle_log(
                "Attempting request",
                method="GET",
                event_key="ATTEMPTS",
                log_level="info",
                service_name="JSONPlaceholder",
                service_method="send_request",
                request_attempt=attempt,
                endpoint=url,
            )
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                clean_data = validator.load(data)

                handle_log(
                    f"Successful response received items: {len(data)}",
                    method="GET",
                    event_key="SUCCESS",
                    log_level="info",
                    service_method="send_request",
                    endpoint=url,
                )

                return clean_data

            except httpx.ConnectError as e:
                wait_time = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                if attempt == MAX_RETRIES:
                    handle_api_error(
                        e,
                        "Unreachable: failed to establish connection to JSONPlaceholder API.",
                        exc_type=APIConnectionException,
                        url=url,
                        method="GET",
                        service_name="JSONPlaceholder",
                        service_method="send_request",
                    )
                handle_log(
                    f"CONNECT ERROR: Request attempt failed, retrying in {wait_time:.2f}s",
                    method="GET",
                    event_key="RETRIES",
                    log_level="warning",
                    service_name="JSONPlaceholder",
                    service_method="send_request",
                    endpoint=url,
                    request_attempt=attempt,
                    error=str(e),
                )
                await asyncio.sleep(wait_time)

            except (httpx.ConnectTimeout, httpx.TimeoutException) as e:
                wait_time = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                if attempt == MAX_RETRIES:
                    handle_api_error(
                        e,
                        "Unreachable: fetch failed due to timeout.",
                        exc_type=APITimeoutException,
                        url=url,
                        method="GET",
                        service_name="JSONPlaceholder",
                        service_method="send_request",
                    )
                handle_log(
                    f"TIMEOUT ERROR: Request attempt failed, retrying in {wait_time:.2f}s",
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
                handle_api_error(
                    e,
                    "Bad status code received from JSONPlaceholder API.",
                    exc_type=APIBadStatusCode,
                    url=url,
                    method="GET",
                    service_name="JSONPlaceholder",
                    service_method="send_request",
                )
            except (httpx.DecodingError, JSONDecodeError) as e:
                handle_api_error(
                    e,
                    "Bad response data received from JSONPlaceholder API.",
                    exc_type=APIJSONDecodeException,
                    url=url,
                    method="GET",
                    service_name="JSONPlaceholder",
                    service_method="send_request",
                )
            except (TypeError, ValueError) as e:
                handle_service_errorV2(
                    e,
                    "Internal Error: Type/Value error.",
                    exc_type=ServiceInternalException,
                    service_method="send_request",
                )
            except ValidationError as e:
                handle_api_error(
                    e,
                    "Validation Error: Invalid data format received from JSONPlaceholder API.",
                    exc_type=APIValidationException,
                    url=url,
                    method="GET",
                    service_name="JSONPlaceholder",
                    service_method="send_request",
                    schema=validator.__class__.__name__,
                )
