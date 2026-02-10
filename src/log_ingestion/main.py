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


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Rapid7 InsightOps Log Ingestion Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch logs for a specific hour
  python -m src.log_ingestion.main \\
      --start-time "2026-02-10T00:00:00Z" \\
      --end-time "2026-02-10T01:00:00Z"

  # Fetch logs for a full day with custom partition date
  python -m src.log_ingestion.main \\
      --start-time "2026-02-10T00:00:00Z" \\
      --end-time "2026-02-10T23:59:59Z" \\
      --partition-date "2026-02-10"

Environment Variables:
  RAPID7_API_KEY          - Required: API authentication key
  RAPID7_API_ENDPOINT     - Required: API base URL
  OUTPUT_DIR              - Required: Output directory for Parquet files
  LOG_LEVEL               - Optional: Logging level (default: INFO)
  BATCH_SIZE              - Optional: Records per batch (default: 1000)
  RATE_LIMIT              - Optional: Max API requests/minute (default: 60)
  RETRY_ATTEMPTS          - Optional: Max retry attempts (default: 3)
  PARQUET_COMPRESSION     - Optional: Compression algorithm (default: snappy)
        """,
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

    return parser.parse_args()


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


def main():
    """Main entry point for the log ingestion service."""
    # Parse command-line arguments
    args = parse_args()

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
        # Load configuration from environment
        config = LogIngestionConfig()

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
