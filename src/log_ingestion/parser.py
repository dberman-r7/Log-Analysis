"""
CSV/Log Parser Module

Handles parsing of log data in CSV format with automatic schema detection
and type inference.

See ADR-0001 for rationale of using pandas for CSV parsing.
"""

from io import StringIO
from typing import Any

import pandas as pd
import structlog

logger = structlog.get_logger()


class LogParser:
    """
    Parse log data from CSV format into pandas DataFrame.

    Provides automatic schema detection from CSV headers or first row,
    type inference, and graceful error handling for malformed data.

    Attributes:
        schema: Cached schema (column names and types) from previous parse
        _last_columns: Column names from last successful parse

    Example:
        parser = LogParser()
        df = parser.parse(csv_string)
        schema = parser.get_schema()
    """

    def __init__(self):
        """Initialize the parser with no schema."""
        self.schema = None
        self._last_columns = None

        logger.info("log_parser_initialized")

    def detect_schema(self, csv_data: str, has_header: bool = True) -> dict[str, Any]:
        """
        Detect schema from CSV data.

        Analyzes the CSV data to determine column names and their types.

        Args:
            csv_data: CSV formatted string
            has_header: Whether the first row contains column headers

        Returns:
            Dictionary mapping column names to their inferred types

        Example:
            schema = parser.detect_schema("timestamp,level,message\\n...")
            # Returns: {"timestamp": "object", "level": "object", ...}
        """
        if not csv_data or csv_data.strip() == "":
            logger.warning("schema_detection_empty_data")
            return {}

        try:
            # Read CSV to detect schema
            df = pd.read_csv(
                StringIO(csv_data),
                header=0 if has_header else None,
                nrows=10,  # Only read first 10 rows for schema detection
            )

            # Build schema dictionary
            schema = {}
            for col in df.columns:
                dtype_name = str(df[col].dtype)
                schema[col] = dtype_name

            logger.info(
                "schema_detected",
                num_columns=len(schema),
                has_header=has_header,
                columns=list(schema.keys()),
            )

            self.schema = schema
            self._last_columns = list(df.columns)

            return schema

        except Exception as e:
            logger.error("schema_detection_failed", error=str(e))
            return {}

    def get_schema(self) -> dict[str, Any] | None:
        """
        Get the cached schema from the last parse operation.

        Returns:
            Cached schema dictionary or None if no schema detected yet
        """
        return self.schema

    def parse(self, csv_data: str, has_header: bool = True) -> pd.DataFrame:
        """
        Parse CSV data into a pandas DataFrame.

        Handles malformed data gracefully, infers data types automatically,
        and caches schema for subsequent calls.

        Args:
            csv_data: CSV formatted string
            has_header: Whether the first row contains column headers.
                       If False and schema is cached, uses cached column names.

        Returns:
            DataFrame containing parsed data (may be empty if data is empty/invalid)

        Raises:
            Does not raise exceptions - returns empty DataFrame on error

        Example:
            df = parser.parse("timestamp,level,message\\n2026-02-10,INFO,Test")
            print(len(df))  # 1
        """
        # Handle empty data
        if not csv_data or csv_data.strip() == "":
            logger.warning("parse_empty_data")
            return pd.DataFrame()

        try:
            # Determine if we should use cached column names
            names = None
            header_arg = 0 if has_header else None

            # If no header and we have cached columns, use them
            if not has_header and self._last_columns:
                names = self._last_columns
                header_arg = None

            # Parse CSV
            df = pd.read_csv(
                StringIO(csv_data),
                header=header_arg,
                names=names,
                # Handle malformed data gracefully
                on_bad_lines="warn",  # Log warnings but continue
                engine="python",  # More flexible parser
            )

            # Infer types automatically (pandas does this by default)
            # But we can optimize by converting specific columns
            df = self._infer_types(df)

            # Cache schema
            if len(df.columns) > 0:
                self.schema = {col: str(df[col].dtype) for col in df.columns}
                self._last_columns = list(df.columns)

            logger.info(
                "parse_success",
                num_rows=len(df),
                num_columns=len(df.columns),
                columns=list(df.columns),
            )

            return df

        except Exception as e:
            logger.error("parse_failed", error=str(e), exc_info=True)
            # Return empty DataFrame on error
            return pd.DataFrame()

    def _infer_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Infer and convert data types for better storage efficiency.

        Attempts to convert columns to appropriate types:
        - Numeric strings -> int or float
        - Timestamp strings -> datetime (optional, can be expensive)

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with optimized types
        """
        if df.empty:
            return df

        # Let pandas infer types with convert_dtypes
        # This is more efficient than manual conversion
        try:
            # Use infer_objects to try converting object columns to better types
            df = df.infer_objects()

            # Try to convert numeric columns that might be strings
            for col in df.columns:
                if df[col].dtype == "object":
                    # Try numeric conversion
                    try:
                        df[col] = pd.to_numeric(df[col], errors="ignore")
                    except Exception:
                        pass  # Keep as string if conversion fails

            logger.debug("type_inference_complete", dtypes=df.dtypes.to_dict())

        except Exception as e:
            logger.warning("type_inference_failed", error=str(e))
            # Return original dataframe if type inference fails

        return df
