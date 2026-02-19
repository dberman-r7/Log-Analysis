"""Rapid7 InsightOps Log Ingestion Service.

This package provides a service to pull logs from the Rapid7 InsightOps API
and save them to Apache Parquet files for analytics.

It also centralizes structlog configuration for consistent JSON structured logs.
Tests may override structlog configuration for capturing events.
"""

from __future__ import annotations

__version__ = "0.1.0"

import logging

import structlog


def _configure_logging() -> None:
    """Configure structlog to emit into stdlib logging.

    Tests rely on pytest's `caplog` fixture, which captures records from the
    standard `logging` module.

    We configure structlog to *forward* events into stdlib logging by ending
    the processor chain with `wrap_for_formatter` and using a stdlib
    `ProcessorFormatter`.
    """

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.INFO)

    pre_chain = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=pre_chain,
    )

    for handler in root.handlers:
        handler.setFormatter(formatter)

    structlog.configure(
        processors=[
            *pre_chain,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


_configure_logging()
