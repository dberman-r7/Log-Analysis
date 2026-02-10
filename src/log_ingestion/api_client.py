"""
Rapid7 InsightOps API Client

Handles authentication, request/response, retry logic, and rate limiting
for interactions with the Rapid7 InsightOps API.

See ADR-0001 for rationale of using requests library.
"""

import time
from typing import Any

import requests
import structlog

from .config import LogIngestionConfig

logger = structlog.get_logger()


class Rapid7ApiClient:
    """
    Client for interacting with Rapid7 InsightOps API.

    Provides methods to fetch logs with automatic retry logic,
    rate limiting, and comprehensive error handling.

    Attributes:
        config: Configuration object with API credentials and settings
        session: Persistent HTTP session with authentication headers
        last_request_time: Timestamp of last API request for rate limiting

    Example:
        config = LogIngestionConfig()
        client = Rapid7ApiClient(config)
        logs = client.fetch_logs("2026-02-10T00:00:00Z", "2026-02-10T01:00:00Z")
    """

    def __init__(self, config: LogIngestionConfig):
        """
        Initialize the API client with configuration.

        Args:
            config: LogIngestionConfig object with API credentials and settings
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.rapid7_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "log-ingestion-service/0.1.0",
            }
        )
        self.last_request_time = 0.0

        logger.info(
            "api_client_initialized",
            endpoint=str(config.rapid7_api_endpoint),
            rate_limit=config.rate_limit,
            retry_attempts=config.retry_attempts,
        )

    def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limiting between API requests.

        Sleeps if necessary to maintain the configured rate limit.
        Rate limit is specified in requests per minute.
        """
        if self.last_request_time > 0:
            # Calculate minimum time between requests (in seconds)
            min_interval = 60.0 / self.config.rate_limit
            elapsed = time.time() - self.last_request_time

            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug("rate_limit_sleep", sleep_seconds=sleep_time)
                time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _retry_with_backoff(self, func, *args, max_retries: int = None, **kwargs) -> Any:
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            max_retries: Maximum retry attempts (defaults to config.retry_attempts)
            **kwargs: Keyword arguments for func

        Returns:
            Result of successful function execution

        Raises:
            Last exception encountered if all retries exhausted
        """
        if max_retries is None:
            max_retries = self.config.retry_attempts

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as e:
                last_exception = e
                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s, 8s, ...
                    sleep_time = 2**attempt
                    logger.warning(
                        "retry_network_error",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        sleep_seconds=sleep_time,
                        error=str(e),
                    )
                    time.sleep(sleep_time)
                else:
                    logger.error(
                        "retry_exhausted_network_error",
                        attempts=attempt + 1,
                        error=str(e),
                    )
                    raise
            except requests.exceptions.HTTPError as e:
                # Check for retriable HTTP errors (5xx server errors)
                status_code = None
                if hasattr(e, "response") and e.response is not None:
                    status_code = e.response.status_code
                    if 500 <= status_code < 600:
                        # Server error - retry
                        last_exception = e
                        if attempt < max_retries:
                            sleep_time = 2**attempt
                            logger.warning(
                                "retry_server_error",
                                attempt=attempt + 1,
                                status_code=status_code,
                                sleep_seconds=sleep_time,
                            )
                            time.sleep(sleep_time)
                            continue
                # Non-retriable HTTP error (4xx) - raise immediately
                logger.error("http_error", status_code=status_code, error=str(e))
                raise

        # If we get here, all retries exhausted
        if last_exception:
            raise last_exception

    def fetch_logs(self, start_time: str, end_time: str) -> dict[str, Any]:
        """
        Fetch logs from Rapid7 InsightOps API for specified time range.

        Handles rate limiting, retries with exponential backoff, and
        special handling for rate limit (429) responses.

        Args:
            start_time: ISO 8601 timestamp for start of time range
            end_time: ISO 8601 timestamp for end of time range

        Returns:
            Dictionary containing logs and pagination info from API response

        Raises:
            requests.exceptions.HTTPError: For non-retriable HTTP errors (4xx)
            requests.exceptions.ConnectionError: For network connectivity issues
            requests.exceptions.Timeout: For request timeouts

        Example:
            logs = client.fetch_logs(
                "2026-02-10T00:00:00Z",
                "2026-02-10T01:00:00Z"
            )
        """
        logger.info("fetch_logs_start", start_time=start_time, end_time=end_time)

        # Enforce rate limiting
        self._enforce_rate_limit()

        # Build request parameters
        params = {"start_time": start_time, "end_time": end_time}

        url = f"{self.config.rapid7_api_endpoint}/logs"

        def make_request():
            """Inner function for retry logic"""
            response = self.session.get(url, params=params, timeout=30)

            # Handle rate limiting (429)
            while response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                logger.warning("rate_limit_hit", retry_after_seconds=retry_after)
                time.sleep(retry_after)
                # Retry after waiting
                response = self.session.get(url, params=params, timeout=30)

            # Raise for HTTP errors (4xx, 5xx)
            response.raise_for_status()

            logger.info(
                "fetch_logs_success",
                status_code=response.status_code,
                start_time=start_time,
                end_time=end_time,
            )

            return response.json()

        # Execute with retry logic
        return self._retry_with_backoff(make_request)
