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

    def fetch_logs(self, start_time: str, end_time: str) -> str:
        """
        Fetch logs from Rapid7 InsightOps API for specified time range.

        Handles rate limiting, retries with exponential backoff, special
        handling for rate limit (429) responses, and pagination support.

        Args:
            start_time: ISO 8601 timestamp for start of time range
            end_time: ISO 8601 timestamp for end of time range

        Returns:
            str: CSV-formatted log data (all pages concatenated)

        Raises:
            requests.exceptions.HTTPError: For non-retriable HTTP errors (4xx)
            requests.exceptions.ConnectionError: For network connectivity issues
            requests.exceptions.Timeout: For request timeouts

        Example:
            csv_logs = client.fetch_logs(
                "2026-02-10T00:00:00Z",
                "2026-02-10T01:00:00Z"
            )
        """
        logger.info("fetch_logs_start", start_time=start_time, end_time=end_time)

        # Normalize endpoint URL (remove trailing slash to prevent double-slash)
        base_url = str(self.config.rapid7_api_endpoint).rstrip("/")
        url = f"{base_url}/logs"

        # Collect all log data across pages
        all_logs_csv = []
        page_number = 1
        next_page_token = None

        while True:
            # Enforce rate limiting for each page request
            self._enforce_rate_limit()

            # Build request parameters
            params: dict[str, Any] = {
                "start_time": start_time,
                "end_time": end_time,
                "format": "csv",  # Request CSV format explicitly
            }

            # Add batch size if configured
            if hasattr(self.config, "api_batch_size"):
                params["limit"] = self.config.api_batch_size

            # Add pagination token if present
            if next_page_token:
                params["page_token"] = next_page_token

            def make_request(current_params=params, current_page=page_number):
                """Inner function for retry logic"""
                response = self.session.get(url, params=current_params, timeout=30)

                # Handle rate limiting (429)
                while response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    logger.warning(
                        "rate_limit_hit",
                        retry_after_seconds=retry_after,
                        page_number=current_page,
                    )
                    time.sleep(retry_after)
                    # Retry after waiting
                    response = self.session.get(url, params=current_params, timeout=30)

                # Raise for HTTP errors (4xx, 5xx)
                response.raise_for_status()

                logger.info(
                    "fetch_logs_page_success",
                    status_code=response.status_code,
                    start_time=start_time,
                    end_time=end_time,
                    page_number=current_page,
                )

                return response

            # Execute with retry logic
            response = self._retry_with_backoff(make_request)

            # Extract CSV data from response
            # Response could be plain CSV text or JSON with CSV field
            content_type = response.headers.get("Content-Type", "")

            if "text/csv" in content_type or "application/csv" in content_type:
                # Response is direct CSV
                csv_data = response.text
                next_page_token = None  # Check headers for pagination
                if "X-Next-Page-Token" in response.headers:
                    next_page_token = response.headers["X-Next-Page-Token"]
            elif "application/json" in content_type:
                # Response is JSON, extract CSV from 'data' or 'logs' field
                json_data = response.json()
                csv_data = json_data.get("data") or json_data.get("logs", "")

                # Check for pagination token in JSON response
                next_page_token = json_data.get("next_page_token") or json_data.get("next_cursor")
            else:
                # Assume text response is CSV
                csv_data = response.text
                next_page_token = None

            # For first page, include headers; for subsequent pages, skip first line (headers)
            if page_number == 1:
                all_logs_csv.append(csv_data)
            else:
                # Skip header line for subsequent pages
                lines = csv_data.split("\n", 1)
                if len(lines) > 1:
                    all_logs_csv.append(lines[1])

            # Check if there are more pages
            if not next_page_token or not csv_data.strip():
                break

            page_number += 1

        # Combine all pages into single CSV
        combined_csv = "\n".join(all_logs_csv)

        logger.info(
            "fetch_logs_complete",
            start_time=start_time,
            end_time=end_time,
            total_pages=page_number,
            total_size=len(combined_csv),
        )

        return combined_csv
