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

# Add: small stdlib imports for correlation ids and safe URL fingerprints.
import hashlib
import uuid

# Add: timestamp conversion for observability fields.
from datetime import datetime, timezone


def _log() -> structlog.stdlib.BoundLogger:
    """Get a structlog logger bound to this module.

    Using a function (instead of a module-level cached logger instance) ensures that
    if structlog is reconfigured at runtime (common in tests), new log events will
    flow through the current processor chain.
    """

    return structlog.get_logger(__name__)


# Back-compat: some tests patch `src.log_ingestion.api_client.logger`.
# Keep this alias in sync with `_log()` usage.
logger = _log()


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
                # NOTE: provider page sizing is controlled via query parameter `per_page`.
                # We intentionally do not send it as an HTTP header.
            }
        )
        self.last_request_time = 0.0

        _log().info(
            "api_client_initialized",
            region=config.rapid7_data_storage_region,
            retry_attempts=config.retry_attempts,
            rate_limit=config.rate_limit,
            per_page=config.rapid7_per_page,
        )

    @staticmethod
    def _epoch_millis_to_iso8601(ts_millis: Optional[int]) -> Optional[str]:
        """Convert epoch-millis to ISO8601 (UTC, Z suffix) for logs.

        This is used for observability only. It fails soft (returns None) if the
        input is None or invalid.
        """

        if ts_millis is None:
            return None
        try:
            if ts_millis < 0:
                return None
            dt = datetime.fromtimestamp(ts_millis / 1000.0, tz=timezone.utc)
            # Always emit `Z` suffix for UTC.
            return dt.isoformat().replace("+00:00", "Z")
        except Exception:
            return None

    @staticmethod
    def _replace_query_param(url: str, key: str, value: str) -> str:
        """Replace or add a query parameter on a URL.

        Notes:
            - Preserves existing query parameters and fragments.
            - If `key` occurs multiple times, all occurrences are replaced.

        Used for pagination boundary tracking (e.g., advancing `from`).
        """

        from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

        parts = urlsplit(url)
        q = parse_qsl(parts.query, keep_blank_values=True)
        updated = [(k, (value if k == key else v)) for (k, v) in q]
        if not any(k == key for (k, _v) in updated):
            updated.append((key, value))
        new_query = urlencode(updated, doseq=True)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    # --- Debug helpers -------------------------------------------------
    @staticmethod
    def _safe_headers_for_log(headers: dict[str, str]) -> dict[str, str]:
        # Never log secrets.
        redacted = {}
        for k, v in headers.items():
            lk = k.lower()
            if lk in {"x-api-key", "authorization", "proxy-authorization"}:
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = v
        return redacted

    @staticmethod
    def _body_preview(resp: requests.Response, max_chars: int = 800) -> str:
        try:
            text = resp.text
        except Exception:
            return "<unavailable>"
        if text is None:
            return ""
        # Some unit tests mock Response.text with a Mock; coerce to a string safely.
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                return "<unavailable>"
        text = text.strip()
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "...<truncated>"

    @staticmethod
    def _headers_as_dict(resp: requests.Response) -> dict[str, str]:
        """Convert response headers to a plain dict[str, str] for logging.

        `requests.Response.headers` is typically a CaseInsensitiveDict, but unit tests may
        mock it with an arbitrary object. We fail soft here (debug logging only) and
        return an empty dict if conversion isn't possible.
        """

        try:
            raw = getattr(resp, "headers", {})
            if raw is None:
                return {}
            if isinstance(raw, dict):
                return {str(k): str(v) for k, v in raw.items()}
            # Try mapping protocol.
            return {str(k): str(raw[k]) for k in list(raw.keys())}
        except Exception:
            return {}

    @staticmethod
    def _safe_json_summary(value: Any) -> dict[str, Any]:
        """Summarize a JSON-like payload without logging full content.

        This is intended for DEBUG logs during polling to answer:
        - did we get JSON?
        - what are the top-level keys?
        - are there obvious counts indicating results volume?

        Never returns large nested objects.
        """

        try:
            if isinstance(value, dict):
                keys = sorted([str(k) for k in value.keys()])
                counts: dict[str, int] = {}
                # Common places where result counts show up in LogSearch.
                for k in ("count", "events", "messages", "logs", "logsets", "data", "results"):
                    v = value.get(k)
                    if isinstance(v, list):
                        counts[f"len_{k}"] = len(v)
                    elif isinstance(v, int):
                        counts[k] = v

                # Common pagination/state signals.
                links = value.get("links")
                link_rels: list[str] = []
                if isinstance(links, list):
                    for li in links:
                        if isinstance(li, dict) and "rel" in li:
                            rel = li.get("rel")
                            if isinstance(rel, str):
                                link_rels.append(rel)

                out: dict[str, Any] = {"type": "dict", "keys": keys}
                if counts:
                    out["counts"] = counts
                if link_rels:
                    out["link_rels"] = sorted(list(set(link_rels)))
                return out

            if isinstance(value, list):
                return {"type": "list", "length": len(value)}

            if value is None:
                return {"type": "null"}

            return {"type": type(value).__name__}
        except Exception:
            return {"type": "<unavailable>"}

    @staticmethod
    def _event_count_from_body(body: Any) -> Optional[int]:
        """Best-effort count of events in a LogSearch page body."""

        if not isinstance(body, dict):
            return None
        events = body.get("events")
        if isinstance(events, list):
            return len(events)
        return None

    @staticmethod
    def _page_max_event_timestamp_millis(body: Any) -> Optional[int]:
        """Return the max event `timestamp` (epoch-millis) from a completed page.

        REQ-027: Operators need to see progress through the dataset, not just page counts.

        Notes:
        - The Rapid7 Log Search event schema commonly includes an integer `timestamp`.
        - We fail soft (return None) when the field isn't present or isn't int-like.
        """

        if not isinstance(body, dict):
            return None
        events = body.get("events")
        if not isinstance(events, list) or not events:
            return None

        max_ts: Optional[int] = None
        for ev in events:
            if not isinstance(ev, dict):
                continue
            ts = ev.get("timestamp")
            if isinstance(ts, int):
                candidate = ts
            elif isinstance(ts, str):
                try:
                    candidate = int(ts)
                except ValueError:
                    continue
            else:
                continue

            if candidate < 0:
                continue

            if max_ts is None or candidate > max_ts:
                max_ts = candidate

        return max_ts

    @staticmethod
    def _page_min_event_timestamp_millis(body: Any) -> Optional[int]:
        """Return the min event `timestamp` (epoch-millis) from a completed page.

        Complements REQ-027 by making it easier to see whether pages are within
        the requested query window and whether pagination is advancing over time.

        Notes:
        - We fail soft (return None) when the field isn't present or isn't int-like.
        """

        if not isinstance(body, dict):
            return None
        events = body.get("events")
        if not isinstance(events, list) or not events:
            return None

        min_ts: Optional[int] = None
        for ev in events:
            if not isinstance(ev, dict):
                continue
            ts = ev.get("timestamp")
            if isinstance(ts, int):
                candidate = ts
            elif isinstance(ts, str):
                try:
                    candidate = int(ts)
                except ValueError:
                    continue
            else:
                continue

            if candidate < 0:
                continue

            if min_ts is None or candidate < min_ts:
                min_ts = candidate

        return min_ts

    def _enforce_rate_limit(self) -> None:
        if self.last_request_time > 0:
            min_interval = 60.0 / self.config.rate_limit
            elapsed = time.time() - self.last_request_time
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                _log().debug("rate_limit_sleep", sleep_seconds=sleep_time)
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
            start = time.time()
            try:
                _log().debug(
                    "http_get_start",
                    url=url,
                    params=params,
                )
                resp = self.session.get(url, params=params, timeout=30)
                duration_ms = int((time.time() - start) * 1000)

                headers_dict = self._headers_as_dict(resp)

                # Log response diagnostics to help triage 404/401/429 issues.
                _log().debug(
                    "http_get_complete",
                    url=url,
                    params=params,
                    status_code=resp.status_code,
                    duration_ms=duration_ms,
                    rate_limit_remaining=headers_dict.get("X-RateLimit-Remaining"),
                    rate_limit_reset=headers_dict.get("X-RateLimit-Reset"),
                    retry_after=headers_dict.get("Retry-After"),
                    response_headers=self._safe_headers_for_log(headers_dict),
                )

                if resp.status_code >= 400:
                    _log().debug(
                        "http_get_error_body_preview",
                        url=url,
                        status_code=resp.status_code,
                        body_preview=self._body_preview(resp),
                    )

                return resp
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                duration_ms = int((time.time() - start) * 1000)
                attempts += 1
                if attempts >= self.config.retry_attempts:
                    _log().error(
                        "http_get_failed",
                        url=url,
                        params=params,
                        attempt=attempts,
                        max_attempts=self.config.retry_attempts,
                        duration_ms=duration_ms,
                        error=str(e),
                        exc_info=True,
                    )
                    raise
                _log().warning(
                    "logsearch_request_retry",
                    url=url,
                    attempt=attempts,
                    max_attempts=self.config.retry_attempts,
                    backoff_seconds=backoff,
                    duration_ms=duration_ms,
                    error=str(e),
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 2.0)

    @staticmethod
    def _links_map(body: dict[str, Any]) -> dict[str, str]:
        """Convert response links to a simple map for easy lookup.

        REQ-014: pagination is driven solely by `links[rel=Next]`.
        """

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

    def _has_next_page(self, body: Any) -> bool:
        """Return True when a completed Log Search page has a Next link.

        REQ-014: pagination is driven solely by `links[rel=Next]`.
        """

        if not isinstance(body, dict):
            return False
        try:
            links = self._links_map(body)
        except Exception as e:
            # Fail loudly: pagination signals are malformed.
            raise ValueError(f"Invalid Log Search response while checking pagination: {e}")
        return "Next" in links

    def _get_next_page(self, completed_page_resp: requests.Response) -> requests.Response:
        """Fetch the next page seed response using `links[rel=Next]`.

        The Log Search API may return 202 with a `Self` continuation for the next page,
        so the caller must run `_poll_request_to_completion()` on the returned response.
        """

        try:
            body = completed_page_resp.json()
        except Exception as e:
            raise ValueError(f"Unable to parse Log Search page JSON for pagination: {e}")

        if not isinstance(body, dict):
            raise ValueError("Invalid Log Search response: expected JSON object for pagination.")

        links = self._links_map(body)
        next_url = links.get("Next")
        if not next_url:
            raise ValueError("No Next link available on completed page.")

        resp = self._request_get(next_url)
        if resp.status_code == 429:
            self._raise_rate_limited(resp)
        resp.raise_for_status()
        return resp

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

    def _poll_request_to_completion(
        self,
        initial_resp: requests.Response,
        *,
        fetch_id: Optional[str] = None,
        page_num: Optional[int] = None,
    ) -> requests.Response:
        """Poll a Log Search query until it completes.

        Fail-loudly safeguards:
        - Max poll count (prevents infinite loops on malformed responses)
        - Max wall time (prevents stuck processes when remote keeps returning rel=Self)
        - Detect a stuck continuation URL (Self link not changing for too long)

        Observability:
        - Emits INFO-level progress every N polls (configurable) so long-running
          queries don't look hung.

        - When provided, includes `fetch_id` and `page_num` fields so operators can
          correlate polling progress back to a specific pagination page.
        """

        self._raise_rate_limited(initial_resp)

        # Parse once for the initial response.
        body = initial_resp.json()
        if not self._is_query_in_progress(body):
            _log().debug(
                "logsearch_poll_not_needed",
                fetch_id=fetch_id,
                page_num=page_num,
                status_code=initial_resp.status_code,
                response_headers=self._safe_headers_for_log(
                    self._headers_as_dict(initial_resp)
                ),
                body_preview=self._body_preview(initial_resp),
                body_summary=self._safe_json_summary(body),
                body_event_count=self._event_count_from_body(body),
            )
            # Cache parsed body so callers don't need to call resp.json() again.
            try:
                setattr(initial_resp, "_cached_json", body)
            except Exception:
                pass
            return initial_resp

        poll_delay = 0.5
        max_poll_delay = 6.0
        max_poll_iterations = int(self.config.poll_max_iterations)
        max_wall_seconds = int(self.config.poll_max_wall_seconds)
        progress_every = int(self.config.poll_progress_log_every)
        started_at = time.time()

        links = self._links_map(body)
        last_self_url: Optional[str] = links.get("Self")
        same_self_url_count = 0
        max_same_self_url_iterations = max(10, int(max_poll_iterations // 2))

        _log().info(
            "logsearch_poll_start",
            fetch_id=fetch_id,
            page_num=page_num,
            self_url=last_self_url,
            max_poll_iterations=max_poll_iterations,
            max_wall_seconds=max_wall_seconds,
            poll_delay_seconds=poll_delay,
            progress_every=progress_every,
            max_same_self_url_iterations=max_same_self_url_iterations,
        )

        resp: requests.Response = initial_resp
        poll_count = 0

        # Start polling by requesting the Self URL immediately; the initial response is
        # typically a 202 with no events.
        if not last_self_url:
            raise ValueError(
                "Invalid Log Search response: expected rel=Self while query in progress"
            )

        resp = self._request_get(last_self_url)
        self._raise_rate_limited(resp)
        try:
            body = resp.json()
        except Exception as e:
            _log().error(
                "logsearch_poll_json_parse_failed",
                fetch_id=fetch_id,
                page_num=page_num,
                poll_count=poll_count,
                elapsed_seconds=time.time() - started_at,
                error=str(e),
                body_preview=self._body_preview(resp),
                exc_info=True,
            )
            raise

        while True:
            elapsed = time.time() - started_at
            resp_headers = self._headers_as_dict(resp)
            _log().info(
                "logsearch_poll_response_received",
                fetch_id=fetch_id,
                page_num=page_num,
                poll_count=poll_count + 1,
                elapsed_seconds=elapsed,
                self_url=last_self_url,
                status_code=resp.status_code,
                response_headers=self._safe_headers_for_log(resp_headers),
                content_length=resp_headers.get("Content-Length"),
                body_event_count=self._event_count_from_body(body),
                body_summary=self._safe_json_summary(body),
                body_preview=self._body_preview(resp),
            )

            if resp.status_code == 429:
                self._raise_rate_limited(resp)
                _log().warning(
                    "logsearch_poll_rate_limited",
                    fetch_id=fetch_id,
                    page_num=page_num,
                    poll_count=poll_count + 1,
                    elapsed_seconds=elapsed,
                    rate_limit_reset=resp_headers.get("X-RateLimit-Reset"),
                    retry_after=resp_headers.get("Retry-After"),
                )

            resp.raise_for_status()

            if not isinstance(body, dict):
                raise ValueError("Invalid Log Search response: expected JSON object body")

            if not self._is_query_in_progress(body):
                _log().info(
                    "logsearch_poll_complete",
                    fetch_id=fetch_id,
                    page_num=page_num,
                    poll_count=poll_count + 1,
                    elapsed_seconds=elapsed,
                    status_code=resp.status_code,
                    body_summary=self._safe_json_summary(body),
                    body_event_count=self._event_count_from_body(body),
                )
                try:
                    setattr(resp, "_cached_json", body)
                except Exception:
                    pass
                return resp

            poll_count += 1
            elapsed = time.time() - started_at
            if poll_count >= max_poll_iterations or elapsed > max_wall_seconds:
                _log().error(
                    "logsearch_poll_timeout",
                    fetch_id=fetch_id,
                    page_num=page_num,
                    poll_count=poll_count,
                    elapsed_seconds=elapsed,
                    max_poll_iterations=max_poll_iterations,
                    max_wall_seconds=max_wall_seconds,
                )
                raise TimeoutError(
                    "Log Search query polling exceeded safety limits. "
                    "This likely indicates a long-running query, a stuck continuation URL, "
                    "or an unexpected response shape. "
                    f"poll_count={poll_count}, elapsed_seconds={elapsed:.1f}."
                )

            links = self._links_map(body)
            self_url = links.get("Self")
            if not self_url:
                raise ValueError(
                    "Invalid Log Search response: expected rel=Self while query in progress"
                )

            if self_url == last_self_url:
                same_self_url_count += 1
                if same_self_url_count >= max_same_self_url_iterations:
                    _log().error(
                        "logsearch_poll_stuck_self_url",
                        fetch_id=fetch_id,
                        page_num=page_num,
                        poll_count=poll_count,
                        elapsed_seconds=elapsed,
                        self_url=self_url,
                        same_self_url_count=same_self_url_count,
                        max_same_self_url_iterations=max_same_self_url_iterations,
                    )
                    raise RuntimeError(
                        "Log Search polling appears stuck (Self URL not changing)."
                    )
            else:
                same_self_url_count = 0
                last_self_url = self_url

            if progress_every > 0 and poll_count % progress_every == 0:
                _log().info(
                    "logsearch_poll_progress",
                    fetch_id=fetch_id,
                    page_num=page_num,
                    poll_count=poll_count,
                    elapsed_seconds=elapsed,
                    self_url=self_url,
                )

            time.sleep(poll_delay)
            poll_delay = min(poll_delay * 1.2, max_poll_delay)

            resp = self._request_get(self_url)
            self._raise_rate_limited(resp)

            try:
                body = resp.json()
            except Exception as e:
                _log().error(
                    "logsearch_poll_json_parse_failed",
                    fetch_id=fetch_id,
                    page_num=page_num,
                    poll_count=poll_count,
                    elapsed_seconds=time.time() - started_at,
                    error=str(e),
                    body_preview=self._body_preview(resp),
                    exc_info=True,
                )
                raise

    @staticmethod
    def _response_json_cached(resp: requests.Response) -> Any:
        """Return response JSON, using a cached copy when present.

        `_poll_request_to_completion()` stores the parsed body on the response as `_cached_json`
        to avoid re-parsing (and to support mocked responses in tests).
        """

        try:
            cached = getattr(resp, "_cached_json", None)
            if cached is not None:
                return cached
        except Exception:
            pass
        return resp.json()

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

        _log().info("logsearch_list_logs_request", region=self.config.rapid7_data_storage_region)

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

        _log().info("logsearch_list_logs_complete", count=len(out))
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

        _log().info(
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

        _log().info("logsearch_list_log_sets_complete", count=len(out))
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

        guidance = (
            "Per-logset membership endpoints are unsupported in this environment. "
            "Use list_log_sets() and the embedded logs_info membership instead."
        )

        # Always raises; keep a `return` stub for type-checkers.
        raise ValueError(guidance)

        return []

    def fetch_logs(self, start_time: str, end_time: str) -> str:
        """Fetch Log Search results for a time range.

        Provider expects from/to in epoch millis.

        Returns:
            A JSON string containing an aggregated representation of all pages.
        """

        fetch_id = str(uuid.uuid4())
        fetch_started_at = time.time()

        # The service layer (REQ-023) will pass epoch-millis strings. Some unit tests
        # send ISO8601; we don't parse here, but we can still log requested window
        # in both raw and int-converted forms when possible.
        def _to_int_or_none(v: str) -> Optional[int]:
            try:
                return int(v)
            except Exception:
                return None

        requested_from_millis = _to_int_or_none(start_time)
        requested_to_millis = _to_int_or_none(end_time)

        base = f"https://{self.config.rapid7_data_storage_region}.rest.logs.insight.rapid7.com"
        url = f"{base}/query/logs/{self.config.rapid7_log_key}"

        params = {
            "from": start_time,
            "to": end_time,
            "query": self.config.rapid7_query,
            # REQ-028: per_page must be controlled via query param.
            "per_page": str(self.config.rapid7_per_page),
        }

        logger.info(
            "logsearch_fetch_start",
            fetch_id=fetch_id,
            region=self.config.rapid7_data_storage_region,
            log_key=self.config.rapid7_log_key,
            from_ms=start_time,
            to_ms=end_time,
            requested_from_millis=requested_from_millis,
            requested_to_millis=requested_to_millis,
            requested_from_iso=self._epoch_millis_to_iso8601(requested_from_millis),
            requested_to_iso=self._epoch_millis_to_iso8601(requested_to_millis),
            query_present=bool(self.config.rapid7_query),
        )

        logger.info(
            "logsearch_query_submitted",
            fetch_id=fetch_id,
            region=self.config.rapid7_data_storage_region,
            log_key=self.config.rapid7_log_key,
            url=url,
            params=params,
            effective_per_page=str(self.config.rapid7_per_page),
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
                    status_code=resp.status_code,
                    body_preview=self._body_preview(resp),
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
                _log().warning(
                    "logsearch_rate_limited",
                    secs_until_reset=e.secs_until_reset,
                    attempt=attempts,
                    max_attempts=self.config.retry_attempts,
                )
                _log().info(
                    "logsearch_rate_limit_sleep",
                    sleep_seconds=e.secs_until_reset,
                    attempt=attempts,
                )
                time.sleep(e.secs_until_reset)
                if attempts > self.config.retry_attempts:
                    raise

        # Poll the initial query request to completion.
        page_num = 1
        page_started_at = time.time()

        logger.info(
            "logsearch_page_start",
            fetch_id=fetch_id,
            page_num=page_num,
            requested_from_millis=requested_from_millis,
            requested_to_millis=requested_to_millis,
            requested_from_iso=self._epoch_millis_to_iso8601(requested_from_millis),
            requested_to_iso=self._epoch_millis_to_iso8601(requested_to_millis),
        )

        page_resp = self._poll_request_to_completion(resp, fetch_id=fetch_id, page_num=page_num)

        pages: list[dict[str, Any]] = []
        body = self._response_json_cached(page_resp)
        pages.append(body)

        events_total: int = 0
        first_count = self._event_count_from_body(body)
        if isinstance(first_count, int):
            events_total += first_count

        fetch_min_event_ts: Optional[int] = self._page_min_event_timestamp_millis(body)
        fetch_max_event_ts: Optional[int] = self._page_max_event_timestamp_millis(body)

        links = self._links_map(body) if isinstance(body, dict) else {}
        next_url = links.get("Next")

        logger.info(
            "logsearch_page_complete",
            fetch_id=fetch_id,
            page_num=page_num,
            page_latency_ms=int((time.time() - page_started_at) * 1000),
            event_count=self._event_count_from_body(body),
            page_min_event_timestamp=self._page_min_event_timestamp_millis(body),
            page_max_event_timestamp=self._page_max_event_timestamp_millis(body),
            page_min_event_timestamp_iso=self._epoch_millis_to_iso8601(
                self._page_min_event_timestamp_millis(body)
            ),
            page_max_event_timestamp_iso=self._epoch_millis_to_iso8601(
                self._page_max_event_timestamp_millis(body)
            ),
            requested_from_millis=requested_from_millis,
            requested_to_millis=requested_to_millis,
            requested_from_iso=self._epoch_millis_to_iso8601(requested_from_millis),
            requested_to_iso=self._epoch_millis_to_iso8601(requested_to_millis),
            events_total=events_total,
            has_next=self._has_next_page(body),
            next_url_present=bool(next_url),
        )

        # Pagination contract (REQ-014): follow `Next` from the most recent completed page.
        # We do not attempt to interpret/advance time boundaries in the client.
        last_next_url: Optional[str] = None
        seen_next_url_count = 0
        max_pages = int(getattr(self.config, "max_pages", 10_000))

        while self._has_next_page(body):
            if page_num >= max_pages:
                logger.error(
                    "logsearch_pagination_page_limit_exceeded",
                    fetch_id=fetch_id,
                    page_num=page_num,
                    max_pages=max_pages,
                )
                raise RuntimeError(
                    f"Pagination exceeded safety limit (max_pages={max_pages})."
                )

            links = self._links_map(body)
            next_url = links.get("Next")
            if not next_url:
                logger.error(
                    "logsearch_next_link_missing",
                    fetch_id=fetch_id,
                    page_num=page_num,
                    body_summary=self._safe_json_summary(body),
                )
                raise ValueError("Invalid Log Search response: expected Next link but none found")

            if last_next_url is not None and next_url == last_next_url:
                logger.error(
                    "logsearch_pagination_not_advancing",
                    fetch_id=fetch_id,
                    page_num=page_num + 1,
                    next_url_fingerprint=hashlib.sha256(next_url.encode("utf-8")).hexdigest()[:12],
                )
                raise RuntimeError(
                    "Pagination did not advance (Next URL repeated). "
                    "This indicates an unexpected API response or client bug."
                )

            seen_next_url_count += 1
            logger.info(
                "logsearch_next_page_fetch",
                fetch_id=fetch_id,
                page_num=page_num + 1,
                next_url_fingerprint=hashlib.sha256(next_url.encode("utf-8")).hexdigest()[:12],
                seen_next_url_count=seen_next_url_count,
            )

            last_next_url = next_url
            page_num += 1

            page_started_at = time.time()
            logger.info(
                "logsearch_page_start",
                fetch_id=fetch_id,
                page_num=page_num,
                requested_from_millis=requested_from_millis,
                requested_to_millis=requested_to_millis,
                requested_from_iso=self._epoch_millis_to_iso8601(requested_from_millis),
                requested_to_iso=self._epoch_millis_to_iso8601(requested_to_millis),
            )

            # Fetch the seed response for the next page and poll it to completion.
            next_seed = self._request_get(next_url)
            if next_seed.status_code == 429:
                self._raise_rate_limited(next_seed)
            next_seed.raise_for_status()

            page_resp = self._poll_request_to_completion(next_seed, fetch_id=fetch_id, page_num=page_num)
            body = self._response_json_cached(page_resp)
            pages.append(body)

            page_count = self._event_count_from_body(body)
            if isinstance(page_count, int):
                events_total += page_count

            page_min_ts = self._page_min_event_timestamp_millis(body)
            page_max_ts = self._page_max_event_timestamp_millis(body)
            if page_min_ts is not None:
                fetch_min_event_ts = (
                    page_min_ts
                    if fetch_min_event_ts is None or page_min_ts < fetch_min_event_ts
                    else fetch_min_event_ts
                )
            if page_max_ts is not None:
                fetch_max_event_ts = (
                    page_max_ts
                    if fetch_max_event_ts is None or page_max_ts > fetch_max_event_ts
                    else fetch_max_event_ts
                )

            logger.info(
                "logsearch_page_complete",
                fetch_id=fetch_id,
                page_num=page_num,
                page_latency_ms=int((time.time() - page_started_at) * 1000),
                event_count=self._event_count_from_body(body),
                page_min_event_timestamp=page_min_ts,
                page_max_event_timestamp=page_max_ts,
                page_min_event_timestamp_iso=self._epoch_millis_to_iso8601(page_min_ts),
                page_max_event_timestamp_iso=self._epoch_millis_to_iso8601(page_max_ts),
                requested_from_millis=requested_from_millis,
                requested_to_millis=requested_to_millis,
                requested_from_iso=self._epoch_millis_to_iso8601(requested_from_millis),
                requested_to_iso=self._epoch_millis_to_iso8601(requested_to_millis),
                events_total=events_total,
                has_next=self._has_next_page(body),
                next_url_present=bool(self._links_map(body).get("Next")) if isinstance(body, dict) else False,
            )

        # Emit final summary and return the aggregated JSON payload.
        logger.info(
            "logsearch_fetch_complete",
            fetch_id=fetch_id,
            pages=len(pages),
            events_total=events_total,
            fetch_min_event_timestamp=fetch_min_event_ts,
            fetch_max_event_timestamp=fetch_max_event_ts,
            fetch_min_event_timestamp_iso=self._epoch_millis_to_iso8601(fetch_min_event_ts),
            fetch_max_event_timestamp_iso=self._epoch_millis_to_iso8601(fetch_max_event_ts),
            duration_ms=int((time.time() - fetch_started_at) * 1000),
        )

        logger.info(
            "logsearch_query_complete",
            fetch_id=fetch_id,
            pages=len(pages),
        )

        return json.dumps({"fetch_id": fetch_id, "pages": pages})
