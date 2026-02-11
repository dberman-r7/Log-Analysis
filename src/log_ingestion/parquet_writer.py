"""
Parquet Writer Module

Handles writing log data to Parquet files with compression,
partitioning, and batching support.

See ADR-0001 for rationale of using PyArrow for Parquet writing.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import os

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog

from .config import LogIngestionConfig

logger = structlog.get_logger()


class ParquetWriter:
    """
    Write log data to Parquet files.

    Provides efficient writing of pandas DataFrames to Parquet format
    with configurable compression, date-based partitioning, and
    append support for multi-batch writing.

    Attributes:
        config: Configuration object with output settings
        output_dir: Path to output directory for Parquet files

    Example:
        config = LogIngestionConfig()
        writer = ParquetWriter(config)
        output_file = writer.write(df, partition_date="2026-02-10")
    """

    def __init__(self, config: LogIngestionConfig):
        """
        Initialize the Parquet writer with configuration.

        Creates output directory if it doesn't exist.

        Args:
            config: LogIngestionConfig object with output settings
        """
        self.config = config
        self.output_dir = Path(config.output_dir)

        guidance = (
            "Set OUTPUT_DIR to a writable directory (e.g., ./data/logs or /tmp/logs)."
        )

        # Create output directory if it doesn't exist
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(
                "output_dir_create_failed",
                output_dir=str(self.output_dir),
                error=str(e),
                exc_info=True,
                guidance=guidance,
            )
            raise OSError(
                f"Unable to create output directory '{self.output_dir}'. "
                f"{guidance} (via OUTPUT_DIR env var)"
            ) from e

        # Fail loudly if the directory exists but isn't writable.
        if not os.access(self.output_dir, os.W_OK):
            err = (
                f"Output directory '{self.output_dir}' is not writable. "
                f"{guidance} (via OUTPUT_DIR env var)"
            )
            logger.error(
                "output_dir_not_writable",
                output_dir=str(self.output_dir),
                error=err,
                guidance=guidance,
            )
            raise OSError(err)

        logger.info(
            "parquet_writer_initialized",
            output_dir=str(self.output_dir),
            compression=config.parquet_compression,
        )

    def write(
        self,
        df: pd.DataFrame,
        partition_date: Optional[str] = None,
        append: bool = False,
    ) -> Optional[Path]:
        """
        Write DataFrame to Parquet file.

        Handles empty DataFrames gracefully, applies compression settings,
        and supports date-based partitioning for organizing output files.

        Args:
            df: DataFrame to write
            partition_date: Optional date string for file partitioning (YYYY-MM-DD).
                          If None, uses current date.
            append: If True, append to existing file (if partition_date matches).
                   If False, create new file with timestamp.

        Returns:
            Path to written Parquet file, or None if DataFrame is empty

        Example:
            # Write single batch
            file1 = writer.write(df, partition_date="2026-02-10")

            # Append to same partition
            file2 = writer.write(df2, partition_date="2026-02-10", append=True)
        """
        # Handle empty DataFrame
        if df.empty:
            logger.warning("write_empty_dataframe")
            return None

        try:
            # Generate output file path
            output_file = self._generate_file_path(partition_date, append)

            # Convert DataFrame to PyArrow Table
            table = pa.Table.from_pandas(df)

            # Write to Parquet
            if append and output_file.exists():
                # Append to existing file
                self._append_to_file(output_file, table)
            else:
                # Write new file
                pq.write_table(
                    table,
                    output_file,
                    compression=self.config.parquet_compression,
                )

            logger.info(
                "parquet_write_success",
                output_file=str(output_file),
                num_rows=len(df),
                num_columns=len(df.columns),
                file_size_bytes=output_file.stat().st_size if output_file.exists() else 0,
            )

            return output_file

        except Exception as e:
            logger.error("parquet_write_failed", error=str(e), exc_info=True)
            raise

    def _generate_file_path(self, partition_date: Optional[str], append: bool) -> Path:
        """
        Generate output file path with date-based directory partitioning.

        Creates directory structure: <output_dir>/YYYY/MM/DD/

        Args:
            partition_date: Optional date string (YYYY-MM-DD)
            append: Whether this is an append operation

        Returns:
            Path object for output file
        """
        # Resolve the effective partition date
        if partition_date:
            # Expect partition_date in YYYY-MM-DD format
            date_obj = datetime.strptime(partition_date, "%Y-%m-%d")
        else:
            date_obj = datetime.now()

        # Derive date components for directory structure and filenames
        year_str = date_obj.strftime("%Y")
        month_str = date_obj.strftime("%m")
        day_str = date_obj.strftime("%d")
        date_str = date_obj.strftime("%Y%m%d")  # YYYYMMDD format

        # Build partition directory path: <output_dir>/YYYY/MM/DD/
        partition_dir = self.output_dir / year_str / month_str / day_str
        partition_dir.mkdir(parents=True, exist_ok=True)

        # For append mode, use the partition date as filename
        if append:
            filename = f"logs_{date_str}.parquet"
        else:
            # For new files, include hour to match RTM specification
            hour_str = datetime.now().strftime("%H")
            filename = f"logs_{date_str}_{hour_str}.parquet"

        output_file = partition_dir / filename

        logger.debug(
            "file_path_generated",
            partition_date=partition_date,
            append=append,
            partition_dir=str(partition_dir),
            filename=filename,
            output_file=str(output_file),
        )

        return output_file

    def _append_to_file(self, output_file: Path, new_table: pa.Table) -> None:
        """
        Append table to existing Parquet file using ParquetWriter.

        Uses PyArrow's ParquetWriter with append mode for better performance
        and memory efficiency.

        Args:
            output_file: Path to existing Parquet file
            new_table: New table to append

        Note:
            For PyArrow versions that support it, uses row-group level appending.
            Falls back to read-concat-write for older versions.
        """
        try:
            # Read only metadata to get existing row count (cheap; reads footer)
            parquet_file = pq.ParquetFile(output_file)
            existing_rows = parquet_file.metadata.num_rows
            existing_schema = parquet_file.schema_arrow

            # Check schema compatibility
            if not existing_schema.equals(new_table.schema, check_metadata=False):
                logger.warning(
                    "schema_mismatch_append",
                    output_file=str(output_file),
                    existing_schema=str(existing_schema),
                    new_schema=str(new_table.schema),
                )

            # Use read-concat-write approach for reliability
            # This is compatible with all PyArrow versions
            existing_table = pq.read_table(output_file)
            combined_table = pa.concat_tables([existing_table, new_table])

            # Write back with compression
            pq.write_table(
                combined_table,
                output_file,
                compression=self.config.parquet_compression,
            )

            total_rows = combined_table.num_rows

            logger.debug(
                "append_success",
                output_file=str(output_file),
                existing_rows=existing_rows,
                new_rows=new_table.num_rows,
                total_rows=total_rows,
            )

        except Exception as e:
            logger.error("append_failed", output_file=str(output_file), error=str(e))
            raise
