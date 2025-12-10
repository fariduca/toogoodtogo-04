"""Unit tests for system start and fallback handlers."""

from telegram.ext import CommandHandler, MessageHandler

from src.handlers.system.start_handler import (
    get_default_message_handler,
    get_start_handler,
)


def test_get_start_handler_returns_command_handler():
    handler = get_start_handler()
    assert isinstance(handler, CommandHandler)


def test_get_default_message_handler_returns_message_handler():
    handler = get_default_message_handler()
    assert isinstance(handler, MessageHandler)
