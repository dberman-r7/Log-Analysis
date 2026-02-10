"""
Configuration management for Rapid7 InsightOps Log Ingestion Service

Uses Pydantic for type-safe configuration validation and automatic
loading from environment variables.

See ADR-0001 for rationale of using Pydantic for configuration.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogIngestionConfig(BaseSettings):
    """
    Configuration for the log ingestion service.

    All configuration values can be set via environment variables.
    Required fields must be provided; optional fields have sensible defaults.

    Example:
        # Set environment variables
        export RAPID7_API_KEY="your_key_here"
        export RAPID7_API_ENDPOINT="https://api.rapid7.com/v1"
        export OUTPUT_DIR="/data/logs"

        # Load configuration
        config = LogIngestionConfig()

    Attributes:
        rapid7_api_key: API authentication key (required)
        rapid7_api_endpoint: Base API URL (required)
        output_dir: Directory for Parquet files (required)
        log_level: Logging verbosity level (default: INFO)
        batch_size: Records per batch (default: 1000)
        rate_limit: Max API requests per minute (default: 60)
        retry_attempts: Max retry attempts for failed requests (default: 3)
        parquet_compression: Compression algorithm (default: snappy)
    """

    # Required configuration
    rapid7_api_key: str = Field(
        ...,
        description="Rapid7 API authentication key",
        min_length=1,
    )

    rapid7_api_endpoint: HttpUrl = Field(
        ...,
        description="Rapid7 API base URL (must be valid HTTP/HTTPS URL)",
    )

    output_dir: Path = Field(
        ...,
        description="Directory where Parquet files will be written",
    )

    # Optional configuration with defaults
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level for the service",
    )

    batch_size: int = Field(
        default=1000,
        description="Number of log entries to fetch per API request",
        ge=100,  # Greater than or equal to 100
        le=10000,  # Less than or equal to 10000
    )

    rate_limit: int = Field(
        default=60,
        description="Maximum API requests per minute",
        ge=1,
        le=1000,
    )

    retry_attempts: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed API calls",
        ge=1,
        le=10,
    )

    parquet_compression: Literal["snappy", "gzip", "brotli", "none"] = Field(
        default="snappy",
        description="Compression algorithm for Parquet files",
    )

    model_config = SettingsConfigDict(
        # Load from .env file in development
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow loading from environment variables even without .env file
        case_sensitive=False,
        # Validate default values
        validate_default=True,
        # Extra fields not allowed (strict mode)
        extra="forbid",
    )
