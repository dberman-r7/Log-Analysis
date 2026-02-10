"""
Tests for CSV/Log Parser module

Following TDD approach - these tests are written first (RED phase)
and will fail until the parser module is implemented.
"""

import pandas as pd


def test_parser_detects_schema_from_headers():
    """Test CSV header detection and schema inference"""
    # Arrange
    csv_data = """timestamp,level,message,user_id
2026-02-10T10:00:00Z,INFO,User logged in,12345
2026-02-10T10:00:01Z,ERROR,Authentication failed,67890"""

    # Act
    from src.log_ingestion.parser import LogParser

    parser = LogParser()
    schema = parser.detect_schema(csv_data)

    # Assert
    assert "timestamp" in schema
    assert "level" in schema
    assert "message" in schema
    assert "user_id" in schema
    assert len(schema) == 4


def test_parser_detects_schema_from_first_row():
    """Test schema detection from first data row when headers are data"""
    # Arrange - first row is actual data, not headers
    csv_data = """2026-02-10T10:00:00Z,INFO,User logged in,12345
2026-02-10T10:00:01Z,ERROR,Authentication failed,67890"""

    # Act
    from src.log_ingestion.parser import LogParser

    parser = LogParser()
    # Should auto-generate column names like col_0, col_1, etc.
    schema = parser.detect_schema(csv_data, has_header=False)

    # Assert
    assert len(schema) >= 4  # At least 4 columns detected
    # Check that schema has auto-generated names
    assert "col_0" in schema or "column_0" in schema or 0 in schema


def test_parser_parses_data_correctly():
    """Test data parsing with proper types"""
    # Arrange
    csv_data = """timestamp,level,message,count
2026-02-10T10:00:00Z,INFO,User logged in,1
2026-02-10T10:00:01Z,ERROR,Authentication failed,2
2026-02-10T10:00:02Z,WARNING,Slow query,3"""

    # Act
    from src.log_ingestion.parser import LogParser

    parser = LogParser()
    df = parser.parse(csv_data)

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "timestamp" in df.columns
    assert "level" in df.columns
    assert "message" in df.columns
    assert "count" in df.columns
    # Check data values
    assert df["level"].iloc[0] == "INFO"
    assert df["message"].iloc[2] == "Slow query"


def test_parser_handles_malformed_csv():
    """Test graceful handling of malformed CSV"""
    # Arrange - inconsistent number of columns
    csv_data = """timestamp,level,message
2026-02-10T10:00:00Z,INFO,User logged in,extra_column
2026-02-10T10:00:01Z,ERROR
2026-02-10T10:00:02Z,WARNING,Slow query"""

    # Act
    from src.log_ingestion.parser import LogParser

    parser = LogParser()
    # Should not raise exception, but handle gracefully
    df = parser.parse(csv_data)

    # Assert
    assert isinstance(df, pd.DataFrame)
    # Should have parsed at least some rows
    assert len(df) >= 1


def test_parser_handles_empty_data():
    """Test handling of empty CSV"""
    # Arrange
    csv_data_empty = ""
    csv_data_header_only = "timestamp,level,message"

    # Act & Assert
    from src.log_ingestion.parser import LogParser

    parser = LogParser()

    # Empty data should return empty DataFrame
    df1 = parser.parse(csv_data_empty)
    assert isinstance(df1, pd.DataFrame)
    assert len(df1) == 0

    # Header only should return empty DataFrame with columns
    df2 = parser.parse(csv_data_header_only)
    assert isinstance(df2, pd.DataFrame)
    assert len(df2) == 0
    assert len(df2.columns) == 3


def test_parser_infers_data_types():
    """Test type inference (string, int, float, timestamp)"""
    # Arrange
    csv_data = """timestamp,count,price,message
2026-02-10T10:00:00Z,100,19.99,Product purchased
2026-02-10T10:00:01Z,200,29.99,Item shipped
2026-02-10T10:00:02Z,150,15.50,Order completed"""

    # Act
    from src.log_ingestion.parser import LogParser

    parser = LogParser()
    df = parser.parse(csv_data)

    # Assert
    assert isinstance(df, pd.DataFrame)
    # Check that numeric columns are inferred correctly
    # count should be int or numeric
    assert pd.api.types.is_numeric_dtype(df["count"])
    # price should be float or numeric
    assert pd.api.types.is_numeric_dtype(df["price"])
    # message should be string/object
    assert pd.api.types.is_string_dtype(df["message"]) or pd.api.types.is_object_dtype(
        df["message"]
    )


def test_parser_preserves_schema_across_calls():
    """Test that parser can cache and reuse schema"""
    # Arrange
    csv_data1 = """timestamp,level,message
2026-02-10T10:00:00Z,INFO,First message"""

    csv_data2 = """2026-02-10T10:00:01Z,ERROR,Second message"""

    # Act
    from src.log_ingestion.parser import LogParser

    parser = LogParser()
    df1 = parser.parse(csv_data1)
    schema = parser.get_schema()

    # Parse second batch without headers using cached schema
    df2 = parser.parse(csv_data2, has_header=False)

    # Assert
    assert schema is not None
    assert list(df1.columns) == list(df2.columns)
    assert len(df2) == 1


def test_parser_handles_quoted_fields():
    """Test handling of CSV with quoted fields containing commas"""
    # Arrange
    csv_data = """timestamp,level,message
2026-02-10T10:00:00Z,INFO,"Message with, comma"
2026-02-10T10:00:01Z,ERROR,"Another, message, with commas\""""

    # Act
    from src.log_ingestion.parser import LogParser

    parser = LogParser()
    df = parser.parse(csv_data)

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    # Check that quoted fields are parsed correctly
    assert "," in df["message"].iloc[0]
    assert df["message"].iloc[0] == "Message with, comma"
