from unittest.mock import MagicMock
from collections import Counter
from typing import Any, Dict, List


def is_logged(mock_logger: MagicMock, level: str, message_substr: str = None) -> bool:
    """
    Helper function to check if a log message containing a substring was
    logged at a specific level returns a boolean value.
    """

    log_method = getattr(mock_logger, level)
    if not message_substr:
        return len(log_method.call_args_list) > 0
    return any(message_substr in str(call) for call in log_method.call_args_list)


def count_log_events(logs: List[Dict], service_method: str) -> Dict[str, Any]:
    """
    Helper function to count log event occurrences by their event_key for a specific
    service_method.
    """

    counts = Counter(
        log.get("extra", {}).get("event_key", None)
        for log in logs
        if log.get("extra", {}).get("service_method") == service_method
    )
    return counts
