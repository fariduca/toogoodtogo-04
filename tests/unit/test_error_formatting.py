"""Unit tests for error message formatting (Phase 8)."""

import pytest

from src.handlers import format_error_message, ERROR_TEMPLATES


def test_format_error_message_structure():
    """Test error message follows [emoji] [problem] [action] pattern."""
    error = format_error_message("❌", "Something went wrong", "Try again later")
    
    assert error.startswith("❌")
    assert "Something went wrong" in error
    assert "Try again later" in error
    assert "\n\n" in error  # Should have proper spacing


def test_format_error_message_with_different_emojis():
    """Test error messages work with different emojis."""
    emojis = ["❌", "⚠️", "🔒", "⏰", "🔴"]
    
    for emoji in emojis:
        error = format_error_message(emoji, "Test problem", "Test action")
        assert error.startswith(emoji)


def test_error_template_not_registered():
    """Test not_registered error template."""
    error = ERROR_TEMPLATES["not_registered"]()
    
    assert "❌" in error
    assert "register" in error.lower()
    assert "/start" in error


def test_error_template_permission_denied():
    """Test permission_denied error template."""
    error = ERROR_TEMPLATES["permission_denied"]()
    
    assert "🔒" in error
    assert "permission" in error.lower()


def test_error_template_rate_limit():
    """Test rate_limit error template with dynamic seconds."""
    error = ERROR_TEMPLATES["rate_limit"](30)
    
    assert "⏱️" in error
    assert "30 seconds" in error or "30" in error
    assert "wait" in error.lower()


def test_error_template_offer_expired():
    """Test offer_expired error template with time."""
    error = ERROR_TEMPLATES["offer_expired"]("18:30")
    
    assert "⏰" in error
    assert "18:30" in error
    assert "expired" in error.lower()
    assert "/browse" in error


def test_error_template_offer_not_found():
    """Test offer_not_found error template."""
    error = ERROR_TEMPLATES["offer_not_found"]()
    
    assert "❌" in error
    assert "not found" in error.lower() or "Offer not found" in error


def test_error_template_reservation_not_found():
    """Test reservation_not_found error template."""
    error = ERROR_TEMPLATES["reservation_not_found"]()
    
    assert "❌" in error
    assert "not found" in error.lower() or "Reservation not found" in error
    assert "/myreservations" in error


def test_error_template_insufficient_inventory():
    """Test insufficient_inventory error template."""
    error = ERROR_TEMPLATES["insufficient_inventory"]()
    
    assert "🔴" in error
    assert "reserved" in error.lower()
    assert "/browse" in error


def test_error_template_invalid_input():
    """Test invalid_input error template with dynamic field."""
    error = ERROR_TEMPLATES["invalid_input"]("price", "Must be greater than 0")
    
    assert "❌" in error
    assert "price" in error.lower()
    assert "Must be greater than 0" in error
    assert "try again" in error.lower()


def test_all_error_templates_callable():
    """Test that all error templates can be called."""
    # Templates with no arguments
    simple_templates = [
        "not_registered",
        "permission_denied",
        "offer_not_found",
        "reservation_not_found",
        "insufficient_inventory",
    ]
    
    for template_name in simple_templates:
        assert template_name in ERROR_TEMPLATES
        error = ERROR_TEMPLATES[template_name]()
        assert isinstance(error, str)
        assert len(error) > 0
    
    # Templates with arguments
    assert ERROR_TEMPLATES["rate_limit"](60)
    assert ERROR_TEMPLATES["offer_expired"]("12:00")
    assert ERROR_TEMPLATES["invalid_input"]("field", "requirement")


def test_error_messages_have_emoji():
    """Test that all error messages start with an emoji."""
    # Test simple templates
    for key in ["not_registered", "permission_denied", "offer_not_found"]:
        error = ERROR_TEMPLATES[key]()
        # Should start with an emoji (not alphanumeric)
        assert not error[0].isalnum()
    
    # Test templates with args
    assert not ERROR_TEMPLATES["rate_limit"](30)[0].isalnum()
    assert not ERROR_TEMPLATES["offer_expired"]("18:00")[0].isalnum()


def test_error_messages_have_action():
    """Test that all error messages suggest an action."""
    action_keywords = ["use", "try", "check", "browse", "wait"]
    
    # Test a few templates
    errors = [
        ERROR_TEMPLATES["not_registered"](),
        ERROR_TEMPLATES["offer_expired"]("18:00"),
        ERROR_TEMPLATES["insufficient_inventory"](),
    ]
    
    for error in errors:
        # Should contain at least one action keyword
        has_action = any(keyword in error.lower() for keyword in action_keywords)
        assert has_action, f"Error should suggest an action: {error}"
