"""
Rapid7 InsightOps Log Search API Client

Implements provider Log Search workflow:
- Authenticate using `x-api-key`
- Submit query request with from/to/query params
- Poll `links[rel=Self]` until completion
- Follow `links[rel=Next]` for pagination
- Handle 429 with `X-RateLimit-Reset`

See CR-2026-02-10-002, REQ-012..REQ-015.
"""

import json
import time
from typing import Any, Dict, Optional

import requests
import structlog

from .config import LogIngestionConfig
from .log_selection import LogDescriptor, LogSetDescriptor

logger = structlog.get_logger()


class RateLimitedException(Exception):
    def __init__(self, message: str, secs_until_reset: int):
        super().__init__(message)
        self.secs_until_reset = secs_until_reset


class Rapid7ApiClient:
    def __init__(self, config: LogIngestionConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "x-api-key": config.rapid7_api_key,
                "Content-Type": "application/json",
                "User-Agent": "log-ingestion-service/0.1.0",
            }
        )
        self.last_request_time = 0.0

        logger.info(
            "api_client_initialized",
            region=config.rapid7_data_storage_region,
            retry_attempts=config.retry_attempts,
            rate_limit=config.rate_limit,
        )

    def _enforce_rate_limit(self) -> None:
        if self.last_request_time > 0:
            min_interval = 60.0 / self.config.rate_limit
            elapsed = time.time() - self.last_request_time
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug("rate_limit_sleep", sleep_seconds=sleep_time)
                time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _request_get(
        self, url: str, *, params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """GET with basic retry for transient network failures.

        Retries are bounded by `config.retry_attempts` and use a small exponential backoff.
        """
        attempts = 0
        backoff = 0.25
        while True:
            self._enforce_rate_limit()
            try:
                resp = self.session.get(url, params=params, timeout=30)
                return resp
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                attempts += 1
                if attempts >= self.config.retry_attempts:
                    raise
                logger.warning(
                    "logsearch_request_retry",
                    url=url,
                    attempt=attempts,
                    max_attempts=self.config.retry_attempts,
                    backoff_seconds=backoff,
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 2.0)

    @staticmethod
    def _links_map(body: dict[str, Any]) -> dict[str, str]:
        links = body.get("links")
        if not links:
            return {}
        if not isinstance(links, list):
            raise ValueError("Invalid Log Search response: 'links' must be a list")
        mapped: dict[str, str] = {}
        for link in links:
            if not isinstance(link, dict) or "rel" not in link or "href" not in link:
                raise ValueError(
                    "Invalid Log Search response: each link must contain 'rel' and 'href'"
                )
            mapped[str(link["rel"])] = str(link["href"])
        return mapped

    @classmethod
    def _is_query_in_progress(cls, body: dict[str, Any]) -> bool:
        links = cls._links_map(body)
        if not links:
            # Terminal response (single page) commonly has no links.
            return False
        # Provider spec: Self => still running; Next => page ready.
        if "Self" in links:
            return True
        if "Next" in links:
            return False
        # If links exists but neither rel appears, fail loudly.
        raise ValueError(
            "Invalid Log Search response: 'links' present but missing rel 'Self' or 'Next'"
        )

    @staticmethod
    def _raise_rate_limited(resp: requests.Response) -> None:
        if resp.status_code != 429:
            return

        # Prefer Retry-After when available.
        retry_after = resp.headers.get("Retry-After")
        reset = resp.headers.get("X-RateLimit-Reset")

        def _parse_secs(value: Optional[str]) -> Optional[int]:
            if value is None:
                return None
            try:
                secs = int(value)
            except (TypeError, ValueError):
                return None
            return secs

        secs = _parse_secs(retry_after)
        if secs is None:
            secs = _parse_secs(reset)

        # Bound/validate to avoid hanging on bad headers.
        if secs is None or secs < 1:
            secs = 1
        if secs > 60:
            secs = 60

        raise RateLimitedException(
            "Log Search API key rate limited.",
            secs,
        )

    def _poll_request_to_completion(self, initial_resp: requests.Response) -> requests.Response:
        self._raise_rate_limited(initial_resp)

        body = initial_resp.json()
        if not self._is_query_in_progress(body):
            return initial_resp

        poll_delay = 0.5
        max_poll_delay = 6.0

        links = self._links_map(body)
        while "Self" in links:
            time.sleep(poll_delay)
            resp = self._request_get(links["Self"])
            self._raise_rate_limited(resp)

            body = resp.json()
            if not self._is_query_in_progress(body):
                return resp

            poll_delay = min(poll_delay * 2, max_poll_delay)
            links = self._links_map(body)

        return initial_resp

    @staticmethod
    def _has_next_page(body: dict[str, Any]) -> bool:
        try:
            links = Rapid7ApiClient._links_map(body)
        except ValueError:
            return False
        return "Next" in links

    def _get_next_page(self, resp: requests.Response) -> requests.Response:
        body = resp.json()
        links = self._links_map(body)
        if "Next" not in links:
            raise ValueError("No 'Next' link present")
        return self._request_get(links["Next"])

    def list_logs(self) -> list[LogDescriptor]:
        """List available logs for the configured region.

        Uses the Log Search management API:
        `GET https://{region}.rest.logs.insight.rapid7.com/management/logs`

        Returns:
            A list of LogDescriptor(id, name).

        Raises:
            requests.HTTPError: on non-2xx responses.
            ValueError: on unexpected response shapes.
        """

        base = f"https://{self.config.rapid7_data_storage_region}.rest.logs.insight.rapid7.com"
        url = f"{base}/management/logs"

        logger.info("logsearch_list_logs_request", region=self.config.rapid7_data_storage_region)

        resp = self._request_get(url)
        if resp.status_code == 429:
            self._raise_rate_limited(resp)
        resp.raise_for_status()

        body = resp.json()
        logs = body.get("logs")
        if not isinstance(logs, list):
            raise ValueError("Invalid Log Search response: missing or invalid 'logs' list")

        out: list[LogDescriptor] = []
        for item in logs:
            if not isinstance(item, dict):
                continue
            log_id = item.get("id")
            name = item.get("name")
            if isinstance(log_id, str) and log_id and isinstance(name, str) and name:
                out.append(LogDescriptor(id=log_id, name=name))

        logger.info("logsearch_list_logs_complete", count=len(out))
        return out

    def list_log_sets(self) -> list[LogSetDescriptor]:
        """List available log sets for the configured region.

        Management endpoint:
        `GET https://{region}.rest.logs.insight.rapid7.com/management/logsets`

        Notes:
            Some Rapid7 environments include per-logset membership inline via a
            `logs_info` array on each log set. When present, we parse it for use
            by interactive selection flows.

        Returns:
            List of LogSetDescriptor(id, name, description)

        Raises:
            requests.HTTPError: on non-2xx responses.
            ValueError: on unexpected response shapes.
        """

        base = f"https://{self.config.rapid7_data_storage_region}.rest.logs.insight.rapid7.com"
        url = f"{base}/management/logsets"

        logger.info(
            "logsearch_list_log_sets_request",
            region=self.config.rapid7_data_storage_region,
        )

        resp = self._request_get(url)
        if resp.status_code == 429:
            self._raise_rate_limited(resp)
        resp.raise_for_status()

        body = resp.json()
        logsets = body.get("logsets")
        if not isinstance(logsets, list):
            raise ValueError("Invalid Log Search response: missing or invalid 'logsets' list")

        out: list[LogSetDescriptor] = []
        for item in logsets:
            if not isinstance(item, dict):
                continue
            log_set_id = item.get("id")
            name = item.get("name")
            description = item.get("description")
            if (
                isinstance(log_set_id, str)
                and log_set_id
                and isinstance(name, str)
                and name
            ):
                # Optional embedded membership list
                logs_info = item.get("logs_info")
                embedded_logs: list[LogDescriptor] = []
                if isinstance(logs_info, list):
                    for li in logs_info:
                        if not isinstance(li, dict):
                            continue
                        log_id = li.get("id")
                        log_name = li.get("name")
                        if (
                            isinstance(log_id, str)
                            and log_id
                            and isinstance(log_name, str)
                            and log_name
                        ):
                            embedded_logs.append(LogDescriptor(id=log_id, name=log_name))

                out.append(
                    LogSetDescriptor(
                        id=log_set_id,
                        name=name,
                        description=str(description) if description is not None else "",
                        logs=embedded_logs,
                    )
                )

        logger.info("logsearch_list_log_sets_complete", count=len(out))
        return out

    def list_logs_in_log_set(self, log_set_id: str) -> list[LogDescriptor]:
        """List logs within a specific log set.

        IMPORTANT (repo contract): In this repository's target Rapid7 environment,
        log set membership is provided inline in the response returned by
        `list_log_sets()` via a `logs_info` array.

        The per-logset membership endpoints:
        - `/management/logsets/{id}/logids`
        - `/management/logsets/{id}/logs`
        are not supported in this environment (often 404) and MUST NOT be used.

        This method therefore fails loudly with actionable guidance.

        Args:
            log_set_id: Log set identifier.

        Raises:
            ValueError: always, with guidance to use `list_log_sets()` and embedded `logs_info`.
        """

        if not log_set_id or not str(log_set_id).strip():
            raise ValueError("log_set_id is required")

        raise ValueError(
            "Per-logset membership endpoints are unsupported in this environment. "
            "Use list_log_sets() and the embedded logs_info membership instead."
        )

    def fetch_logs(self, start_time: str, end_time: str) -> str:
        """Fetch Log Search results for a time range.

        Provider expects from/to in epoch millis.

        Returns:
            A JSON string containing an aggregated representation of all pages.
        """

        base = f"https://{self.config.rapid7_data_storage_region}.rest.logs.insight.rapid7.com"
        url = f"{base}/query/logs/{self.config.rapid7_log_key}"

        params = {
            "from": start_time,
            "to": end_time,
            "query": self.config.rapid7_query,
        }

        logger.info(
            "logsearch_query_submitted",
            region=self.config.rapid7_data_storage_region,
            log_key=self.config.rapid7_log_key,
        )

        def do_query() -> requests.Response:
            resp = self._request_get(url, params=params)
            if resp.status_code == 429:
                self._raise_rate_limited(resp)

            if resp.status_code == 404:
                guidance = (
                    "Log Search query endpoint returned 404. This typically indicates a mismatch between "
                    "(a) RAPID7_DATA_STORAGE_REGION, (b) the base URL for your account/region, or (c) an invalid "
                    "RAPID7_LOG_KEY. Confirm the log key by running: python -m src.log_ingestion.main --select-log ... "
                    "and ensure the region matches your Rapid7 environment."
                )
                logger.error(
                    "logsearch_query_endpoint_not_found",
                    url=url,
                    region=self.config.rapid7_data_storage_region,
                    log_key=self.config.rapid7_log_key,
                    guidance=guidance,
                )

            resp.raise_for_status()
            return resp

        attempts = 0
        while True:
            try:
                resp = do_query()
                break
            except RateLimitedException as e:
                attempts += 1
                logger.warning("logsearch_rate_limited", secs_until_reset=e.secs_until_reset)
                time.sleep(e.secs_until_reset)
                if attempts > self.config.retry_attempts:
                    raise

        # Poll the initial query request to completion.
        page_resp = self._poll_request_to_completion(resp)

        pages: list[dict[str, Any]] = []
        body = page_resp.json()
        pages.append(body)

        # Pagination: always follow `Next` from the most recent *completed* page.
        while self._has_next_page(body):
            next_seed = self._get_next_page(page_resp)
            page_resp = self._poll_request_to_completion(next_seed)
            body = page_resp.json()
            pages.append(body)

        aggregated: dict[str, Any] = {"pages": pages}
        return json.dumps(aggregated)
