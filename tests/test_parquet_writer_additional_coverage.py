"""Additional coverage for ParquetWriter error paths.

Governance note:
- Improves coverage without changing production semantics.
- Exercises fail-loudly behavior and internal helpers.
"""

from pathlib import Path

import pandas as pd
import pytest


def test_parquet_writer_raises_when_output_dir_not_writable(monkeypatch, tmp_path: Path) -> None:
    """ParquetWriter should fail loudly when output dir isn't writable."""
    from src.log_ingestion.config import LogIngestionConfig

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Force non-writable regardless of platform FS semantics.
    monkeypatch.setattr("src.log_ingestion.parquet_writer.os.access", lambda *args, **kwargs: False)

    with pytest.raises(OSError):
        from src.log_ingestion.parquet_writer import ParquetWriter

        ParquetWriter(
            LogIngestionConfig(
                rapid7_api_key="k",
                rapid7_log_key="l",
                output_dir=str(out_dir),
            )
        )


def test_parquet_writer_generation_and_empty_df(tmp_path: Path) -> None:
    """Writer should return None on empty dataframe and generate expected paths."""
    from src.log_ingestion.config import LogIngestionConfig
    from src.log_ingestion.parquet_writer import ParquetWriter

    writer = ParquetWriter(
        LogIngestionConfig(
            rapid7_api_key="k",
            rapid7_log_key="l",
            output_dir=str(tmp_path / "out"),
        )
    )

    empty = pd.DataFrame()
    assert writer.write(empty) is None

    path1 = writer._generate_file_path(partition_date="2026-02-10", append=False)
    assert "2026" in str(path1)
    assert path1.name.startswith("logs_")

    path2 = writer._generate_file_path(partition_date="2026-02-10", append=True)
    assert path2.name.endswith(".parquet")
    assert "_" not in path2.stem.split("logs_")[-1]  # append variant has no hour suffix
