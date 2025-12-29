"""Structured logging configuration using structlog."""

import logging
import os
import re
import sys

import structlog

# Pattern to match Telegram bot tokens in URLs and strings
# Format: <bot_id>:<token> e.g., 8392205405:AAGcX5QLzoD6l7gSh4RahBAdYpY8jsSorSI
_BOT_TOKEN_PATTERN = re.compile(r"(\d{8,12}:[A-Za-z0-9_-]{35})")


class TokenRedactingFilter(logging.Filter):
    """Filter that redacts sensitive tokens from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact bot tokens from log message."""
        if record.msg and isinstance(record.msg, str):
            record.msg = _BOT_TOKEN_PATTERN.sub("<BOT_TOKEN_REDACTED>", record.msg)
        if record.args:
            record.args = tuple(
                _BOT_TOKEN_PATTERN.sub("<BOT_TOKEN_REDACTED>", str(arg))
                if isinstance(arg, str)
                else arg
                for arg in record.args
            )
        return True


def _redact_tokens(
    logger: logging.Logger, method_name: str, event_dict: dict
) -> dict:
    """Structlog processor to redact bot tokens from event dictionaries."""
    for key, value in list(event_dict.items()):
        if isinstance(value, str):
            event_dict[key] = _BOT_TOKEN_PATTERN.sub("<BOT_TOKEN_REDACTED>", value)
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    # Create token-redacting filter
    token_filter = TokenRedactingFilter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers and add new one with filter
    root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(token_filter)
    root_logger.addHandler(handler)

    # Also apply filter to httpx and httpcore loggers specifically
    for logger_name in ("httpx", "httpcore", "telegram", "python_telegram_bot"):
        lib_logger = logging.getLogger(logger_name)
        lib_logger.addFilter(token_filter)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_tokens,  # Custom processor to redact tokens
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
