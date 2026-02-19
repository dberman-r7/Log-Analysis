"""Parquet-derived summary generation.

Implements REQ-027.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Union

import pyarrow.parquet as pq
import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class ParquetSummary:
    row_count: int
    columns: List[str]
    timestamp_min: Optional[Any]
    timestamp_max: Optional[Any]


def generate_summary(
    dataset_path: Union[str, Path], timestamp_column: str = "timestamp"
) -> ParquetSummary:
    """Generate a lightweight summary from a parquet file or directory dataset.

    Args:
        dataset_path: Parquet file path or directory dataset.
        timestamp_column: Column to compute min/max for, if present.

    Returns:
        ParquetSummary with row_count, columns (names), and timestamp min/max.
    """

    dataset_path = Path(dataset_path)

    table = pq.read_table(dataset_path)
    row_count = int(table.num_rows)
    columns = list(table.column_names)

    ts_min = None
    ts_max = None
    if timestamp_column in columns and row_count > 0:
        # Read just the timestamp column into pandas for min/max.
        ts_series = table.select([timestamp_column]).to_pandas()[timestamp_column]
        ts_min = ts_series.min()
        ts_max = ts_series.max()

    summary = ParquetSummary(
        row_count=row_count,
        columns=columns,
        timestamp_min=ts_min,
        timestamp_max=ts_max,
    )

    logger.info(
        "parquet_summary_generated",
        dataset_path=str(dataset_path),
        row_count=row_count,
        column_count=len(columns),
        timestamp_column=timestamp_column,
        timestamp_min=str(ts_min) if ts_min is not None else None,
        timestamp_max=str(ts_max) if ts_max is not None else None,
    )

    return summary
