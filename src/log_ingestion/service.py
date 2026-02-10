"""
Log Ingestion Service (Main Orchestration)

Orchestrates the complete log ingestion pipeline:
1. Fetch logs from Rapid7 API
2. Parse CSV data
3. Write to Parquet files

See ADR-0001 for architecture decisions.
"""

from datetime import datetime
from typing import Any, Optional

import structlog

from .api_client import Rapid7ApiClient
from .config import LogIngestionConfig
from .parquet_writer import ParquetWriter
from .parser import LogParser

logger = structlog.get_logger()


class LogIngestionService:
    """
    Main service orchestrating the log ingestion pipeline.

    Coordinates API client, CSV parser, and Parquet writer to fetch logs
    from Rapid7 InsightOps API and store them in Parquet format.

    Attributes:
        config: Configuration object
        api_client: Rapid7 API client
        parser: CSV log parser
        writer: Parquet file writer

    Example:
        config = LogIngestionConfig()
        service = LogIngestionService(config)
        result = service.run("2026-02-10T00:00:00Z", "2026-02-10T01:00:00Z")
    """

    def __init__(self, config: LogIngestionConfig):
        """
        Initialize the log ingestion service.

        Creates and configures all pipeline components.

        Args:
            config: LogIngestionConfig object with service settings
        """
        self.config = config

        # Initialize components
        self.api_client = Rapid7ApiClient(config)
        self.parser = LogParser()
        self.writer = ParquetWriter(config)

        logger.info(
            "service_initialized",
            batch_size=config.batch_size,
            rate_limit=config.rate_limit,
            output_dir=str(config.output_dir),
        )

    def run(
        self, start_time: str, end_time: str, partition_date: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Execute the complete log ingestion pipeline.

        Fetches logs from Rapid7 API, parses CSV data, and writes to Parquet.

        Args:
            start_time: Start timestamp in ISO 8601 format (e.g., "2026-02-10T00:00:00Z")
            end_time: End timestamp in ISO 8601 format
            partition_date: Optional date for file partitioning (YYYY-MM-DD).
                          If None, extracted from start_time.

        Returns:
            Dictionary with pipeline results:
                - output_file: Path to written Parquet file (or None if empty)
                - rows_processed: Number of log rows processed
                - batches_processed: Number of batches processed
                - start_time: Pipeline start time
                - end_time: Pipeline end time

        Raises:
            Exception: If API fetch fails or critical error occurs

        Example:
            result = service.run("2026-02-10T00:00:00Z", "2026-02-10T01:00:00Z")
            print(f"Processed {result['rows_processed']} rows")
        """
        pipeline_start = datetime.now()

        logger.info(
            "pipeline_start",
            start_time=start_time,
            end_time=end_time,
            partition_date=partition_date,
        )

        try:
            # Step 1: Fetch logs from API
            logger.info("pipeline_step_fetch", step=1)
            csv_data = self.api_client.fetch_logs(start_time, end_time)

            # Step 2: Parse CSV data
            logger.info("pipeline_step_parse", step=2)
            df = self.parser.parse(csv_data)

            # Handle empty data
            if df.empty:
                logger.warning("pipeline_empty_data", rows_processed=0)
                return {
                    "output_file": None,
                    "rows_processed": 0,
                    "batches_processed": 0,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                }

            # Determine partition date
            if partition_date is None:
                # Extract date from start_time (format: YYYY-MM-DD)
                partition_date = start_time.split("T")[0]

            # Step 3: Process in batches if needed
            logger.info("pipeline_step_write", step=3)
            batch_size = self.config.batch_size
            total_rows = len(df)
            batches_processed = 0
            output_file = None

            if total_rows <= batch_size:
                # Single batch - write all at once
                output_file = self.writer.write(df, partition_date=partition_date)
                batches_processed = 1
                logger.info(
                    "pipeline_single_batch",
                    rows=total_rows,
                    output_file=str(output_file) if output_file else None,
                )
            else:
                # Multiple batches
                for i in range(0, total_rows, batch_size):
                    batch_df = df.iloc[i : i + batch_size]
                    batch_num = batches_processed + 1

                    # First batch creates file, subsequent batches append
                    append = batches_processed > 0

                    output_file = self.writer.write(
                        batch_df, partition_date=partition_date, append=append
                    )

                    batches_processed += 1

                    logger.info(
                        "pipeline_batch_processed",
                        batch_num=batch_num,
                        batch_rows=len(batch_df),
                        total_batches=((total_rows - 1) // batch_size) + 1,
                    )

            pipeline_end = datetime.now()
            duration = (pipeline_end - pipeline_start).total_seconds()

            logger.info(
                "pipeline_complete",
                rows_processed=total_rows,
                batches_processed=batches_processed,
                output_file=str(output_file) if output_file else None,
                duration_seconds=duration,
            )

            return {
                "output_file": str(output_file) if output_file else None,
                "rows_processed": total_rows,
                "batches_processed": batches_processed,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
            }

        except Exception as e:
            logger.error(
                "pipeline_failed",
                error=str(e),
                start_time=start_time,
                end_time=end_time,
                exc_info=True,
            )
            raise
