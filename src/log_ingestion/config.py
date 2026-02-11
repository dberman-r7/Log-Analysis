"""
Configuration management for Rapid7 InsightOps Log Ingestion Service

Uses Pydantic for type-safe configuration validation and automatic
loading from environment variables.

See ADR-0001 for rationale of using Pydantic for configuration.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogIngestionConfig(BaseSettings):
    """Configuration for the log ingestion service.

    All configuration values can be set via environment variables.
    Required fields must be provided; optional fields have sensible defaults.

    Note:
        This repository targets Python 3.9+, so we avoid PEP604 (X | Y) typing.
    """

    # Required configuration
    rapid7_api_key: str = Field(
        ...,
        description="Rapid7 API authentication key",
        min_length=1,
        alias="RAPID7_API_KEY",
    )

    # Provider Log Search API settings
    rapid7_data_storage_region: Literal["us", "eu", "ca", "ap", "au"] = Field(
        default="eu",
        description="Rapid7 Log Search data storage region (e.g., 'eu')",
        alias="RAPID7_DATA_STORAGE_REGION",
    )

    rapid7_log_key: str = Field(
        ...,
        description="Rapid7 Log Search log key (LOG_KEY) used in /query/logs/{log_key}",
        min_length=1,
        alias="RAPID7_LOG_KEY",
    )

    rapid7_query: str = Field(
        default="",
        description="Log Search query string (provider 'query' parameter)",
        alias="RAPID7_QUERY",
    )

    output_dir: Path = Field(
        default=Path("data") / "logs",
        description="Directory where Parquet files will be written (default: ./data/logs)",
        alias="OUTPUT_DIR",
    )

    # Optional configuration with defaults
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level for the service",
        alias="LOG_LEVEL",
    )

    batch_size: int = Field(
        default=1000,
        description="Number of log entries to fetch per API request",
        ge=100,
        le=10000,
        alias="BATCH_SIZE",
    )

    rate_limit: int = Field(
        default=60,
        description="Maximum API requests per minute",
        ge=1,
        le=1000,
        alias="RATE_LIMIT",
    )

    retry_attempts: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed API calls",
        ge=1,
        le=10,
        alias="RETRY_ATTEMPTS",
    )

    parquet_compression: Literal["snappy", "gzip", "brotli", "none"] = Field(
        default="snappy",
        description="Compression algorithm for Parquet files",
        alias="PARQUET_COMPRESSION",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="forbid",
    )
