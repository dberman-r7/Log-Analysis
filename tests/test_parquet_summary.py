import tempfile

import pandas as pd


def test_summary_includes_row_count_columns_and_timestamp_min_max():
    from src.log_ingestion.parquet_summary import generate_summary

    with tempfile.TemporaryDirectory() as tmpdir:
        df = pd.DataFrame(
            [
                {"timestamp": 10, "message": "a"},
                {"timestamp": 30, "message": "b"},
            ]
        )
        path = f"{tmpdir}/data.parquet"
        df.to_parquet(path)

        summary = generate_summary(path)

        assert summary.row_count == 2
        assert "timestamp" in summary.columns
        assert "message" in summary.columns
        assert summary.timestamp_min == 10
        assert summary.timestamp_max == 30
