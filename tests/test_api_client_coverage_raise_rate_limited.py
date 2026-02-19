"""Coverage tests for rate limiting helper.

Exercises `_raise_rate_limited()` parsing and bounds without making network calls.
"""

from unittest.mock import Mock

import pytest


def test_raise_rate_limited_prefers_retry_after_and_bounds_to_60():
    from src.log_ingestion.api_client import RateLimitedException, Rapid7ApiClient

    resp = Mock()
    resp.status_code = 429
    resp.headers = {
        "Retry-After": "999",  # should be bounded
        "X-RateLimit-Reset": "5",
    }

    with pytest.raises(RateLimitedException) as exc:
        Rapid7ApiClient._raise_rate_limited(resp)

    assert exc.value.secs_until_reset == 60


def test_raise_rate_limited_falls_back_to_reset_and_bounds_min_to_1():
    from src.log_ingestion.api_client import RateLimitedException, Rapid7ApiClient

    resp = Mock()
    resp.status_code = 429
    resp.headers = {
        "Retry-After": "not-an-int",
        "X-RateLimit-Reset": "0",  # should be bounded up
    }

    with pytest.raises(RateLimitedException) as exc:
        Rapid7ApiClient._raise_rate_limited(resp)

    assert exc.value.secs_until_reset == 1
