"""
Main entry point for the Rapid7 InsightOps log ingestion service.

This module provides command-line interface for running the log ingestion
pipeline.

Usage:
    python -m src.log_ingestion.main --start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T23:59:59Z"

Example:
    python -m src.log_ingestion.main \\
        --start-time "2026-02-10T00:00:00Z" \\
        --end-time "2026-02-10T01:00:00Z" \\
        --partition-date "2026-02-10"
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import structlog

from .config import LogIngestionConfig
from .service import LogIngestionService
from .env_utils import upsert_env_var
from .log_selection import choose_log_id, choose_log_set_id
from .api_client import Rapid7ApiClient

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def _ensure_module_execution_context() -> None:
    """Guard against running this file directly (breaks relative imports).

    REQ-020: Users should run this as a module:
      python -m src.log_ingestion.main ...

    Direct execution (`python src/log_ingestion/main.py`) causes relative-import
    errors because the package context isn't established.
    """

    if __name__ == "__main__" and not __package__:
        raise RuntimeError(
            "This module must be executed with an importable package context. "
            "Run: python -m src.log_ingestion.main --start-time ... --end-time ..."
        )


def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Rapid7 InsightOps Log Ingestion Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch logs for a specific hour
  python -m src.log_ingestion.main \
      --start-time "2026-02-10T00:00:00Z" \
      --end-time "2026-02-10T01:00:00Z"

  # Fetch logs for a full day with custom partition date
  python -m src.log_ingestion.main \
      --start-time "2026-02-10T00:00:00Z" \
      --end-time "2026-02-10T23:59:59Z" \
      --partition-date "2026-02-10"

Environment Variables:
  RAPID7_API_KEY               - Required: API authentication key
  RAPID7_DATA_STORAGE_REGION   - Optional: Log Search region (default: eu)
  RAPID7_LOG_KEY               - Optional: Log key for Log Search (default: test-log-key)
  RAPID7_QUERY                 - Optional: Log Search query string (default: empty)
  OUTPUT_DIR                   - Optional: Output directory for Parquet files (default: ./data/logs)

  LOG_LEVEL                    - Optional: Logging level (default: INFO)
  BATCH_SIZE                   - Optional: Records per batch (default: 1000)
  RATE_LIMIT                   - Optional: Max API requests/minute (default: 60)
  RETRY_ATTEMPTS               - Optional: Max retry attempts (default: 3)
  PARQUET_COMPRESSION          - Optional: Compression algorithm (default: snappy)
        """,
    )

    parser.add_argument(
        "--select-log",
        action="store_true",
        help="List available Log Search logs for the configured region and update .env RAPID7_LOG_KEY.",
    )

    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file to update when using --select-log (default: .env)",
    )

    parser.add_argument(
        "--start-time",
        required=True,
        help="Start time for log fetch (ISO 8601 format, e.g., '2026-02-10T00:00:00Z')",
    )

    parser.add_argument(
        "--end-time",
        required=True,
        help="End time for log fetch (ISO 8601 format, e.g., '2026-02-10T23:59:59Z')",
    )

    parser.add_argument(
        "--partition-date",
        help="Partition date for output file (YYYY-MM-DD format). "
        "If not provided, extracted from start_time.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser.parse_args(argv)


def validate_iso8601(timestamp: str) -> bool:
    """
    Validate ISO 8601 timestamp format.

    Args:
        timestamp: Timestamp string to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _run_log_selection(config: LogIngestionConfig, env_file: str) -> int:
    """Interactive helper to choose a log and persist it to the env file."""

    client = Rapid7ApiClient(config)

    # Step 1: list log sets
    log_sets = client.list_log_sets()
    if not log_sets:
        logger.error("logsearch_no_log_sets_found")
        print("No log sets found for this account/region.", file=sys.stderr)
        return 1

    print("\nAvailable log sets:")
    for i, ls in enumerate(log_sets, start=1):
        suffix = f" — {ls.description}" if ls.description else ""
        print(f"  {i:>3}. {ls.name}  ({ls.id}){suffix}")

    log_set_choice = input("\nSelect a log set by number (or paste a log set id): ").strip()

    try:
        selected_log_set_id = choose_log_set_id(log_sets, log_set_choice)
    except ValueError as e:
        logger.error("logsearch_invalid_log_set_selection", error=str(e))
        print(f"Invalid log set selection: {e}", file=sys.stderr)
        return 2

    # Step 2: determine logs within selected log set.
    # In this environment, the log set list response contains `logs_info` already.
    selected_log_set = next((ls for ls in log_sets if ls.id == selected_log_set_id), None)
    logs = list(selected_log_set.logs) if (selected_log_set and selected_log_set.logs) else []

    if not logs:
        logger.error(
            "logsearch_logset_missing_embedded_logs",
            log_set_id=selected_log_set_id,
            note="No logs were present in list_log_sets() response (expected logs_info).",
        )
        print(
            "No logs were provided for the selected log set in the logsets list response.\n"
            "This environment doesn't support per-logset membership endpoints (404).\n"
            "Please ensure the logsets response includes `logs_info`.",
            file=sys.stderr,
        )
        return 1

    logger.info(
        "logsearch_logs_resolved_from_logsets_response",
        log_set_id=selected_log_set_id,
        count=len(logs),
    )

    print("\nAvailable logs in selected log set:")
    for i, log in enumerate(logs, start=1):
        print(f"  {i:>3}. {log.name}  ({log.id})")

    choice = input("\nSelect a log by number (or paste a log id): ").strip()

    try:
        selected_log_id = choose_log_id(logs, choice)
    except ValueError as e:
        logger.error("logsearch_invalid_log_selection", error=str(e))
        print(f"Invalid log selection: {e}", file=sys.stderr)
        return 2

    result = upsert_env_var(Path(env_file), "RAPID7_LOG_KEY", selected_log_id)

    logger.info(
        "logsearch_log_key_updated",
        env_file=str(result.path),
        created=result.created,
    )

    print(f"\nUpdated {result.path} with RAPID7_LOG_KEY={selected_log_id}")
    return 0


def main():
    """Main entry point for the log ingestion service."""
    _ensure_module_execution_context()
    # Parse command-line arguments
    args = parse_args()

    try:
        # Load configuration from environment
        config = LogIngestionConfig()

        if args.select_log:
            sys.exit(_run_log_selection(config, args.env_file))

    except Exception as e:
        # If config can't load, surface that clearly.
        logger.error("config_load_failed", error=str(e), exc_info=True)
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate timestamps
    if not validate_iso8601(args.start_time):
        logger.error("invalid_start_time", start_time=args.start_time)
        print(f"Error: Invalid start_time format: {args.start_time}", file=sys.stderr)
        print("Expected ISO 8601 format, e.g., '2026-02-10T00:00:00Z'", file=sys.stderr)
        sys.exit(1)

    if not validate_iso8601(args.end_time):
        logger.error("invalid_end_time", end_time=args.end_time)
        print(f"Error: Invalid end_time format: {args.end_time}", file=sys.stderr)
        print("Expected ISO 8601 format, e.g., '2026-02-10T23:59:59Z'", file=sys.stderr)
        sys.exit(1)

    # Validate partition date if provided
    if args.partition_date:
        try:
            datetime.strptime(args.partition_date, "%Y-%m-%d")
        except ValueError:
            logger.error("invalid_partition_date", partition_date=args.partition_date)
            print(
                f"Error: Invalid partition_date format: {args.partition_date}",
                file=sys.stderr,
            )
            print("Expected format: YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    logger.info(
        "service_start",
        start_time=args.start_time,
        end_time=args.end_time,
        partition_date=args.partition_date,
    )

    try:

        # Initialize service
        service = LogIngestionService(config)

        # Run pipeline
        result = service.run(
            start_time=args.start_time,
            end_time=args.end_time,
            partition_date=args.partition_date,
        )

        # Log and print results
        logger.info("service_complete", result=result)

        print("\n" + "=" * 60)
        print("Log Ingestion Complete")
        print("=" * 60)
        print(f"Rows processed:    {result['rows_processed']:,}")
        print(f"Batches processed: {result['batches_processed']}")
        print(f"Duration:          {result['duration_seconds']:.2f} seconds")
        if result['output_file']:
            print(f"Output file:       {result['output_file']}")
            # Get file size if it exists
            output_path = Path(result['output_file'])
            if output_path.exists():
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"File size:         {file_size_mb:.2f} MB")
        else:
            print("Output file:       None (no data to process)")
        print("=" * 60)

        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("service_interrupted")
        print("\nService interrupted by user", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        logger.error("service_failed", error=str(e), exc_info=True)
        print(f"\nError: {e}", file=sys.stderr)
        print("\nFor more details, check the logs.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
