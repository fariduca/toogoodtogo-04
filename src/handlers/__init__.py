"""Handlers package - Telegram bot feature plugins."""


def format_error_message(emoji: str, problem: str, action: str) -> str:
    """
    Format error messages following the pattern: [emoji] [problem] [action].
    
    Args:
        emoji: Visual indicator (e.g., "❌", "⚠️", "🔒")
        problem: Clear description of what went wrong
        action: Suggested next step for the user
        
    Returns:
        Formatted error message string
        
    Example:
        >>> format_error_message("❌", "Offer expired", "Browse other deals with /browse")
        "❌ Offer expired\n\nBrowse other deals with /browse"
    """
    return f"{emoji} {problem}\n\n{action}"


# Common error templates
ERROR_TEMPLATES = {
    "not_registered": lambda: format_error_message(
        "❌",
        "You need to register first.",
        "Use /start to begin."
    ),
    "permission_denied": lambda: format_error_message(
        "🔒",
        "You don't have permission to perform this action.",
        "Make sure you're using the correct account."
    ),
    "rate_limit": lambda seconds: format_error_message(
        "⏱️",
        "Too many requests.",
        f"Please wait {seconds} seconds before trying again."
    ),
    "offer_expired": lambda time: format_error_message(
        "⏰",
        f"This offer expired at {time}.",
        "Browse other deals with /browse"
    ),
    "offer_not_found": lambda: format_error_message(
        "❌",
        "Offer not found.",
        "It may have been removed or expired."
    ),
    "reservation_not_found": lambda: format_error_message(
        "❌",
        "Reservation not found.",
        "Check your active reservations with /myreservations"
    ),
    "insufficient_inventory": lambda: format_error_message(
        "🔴",
        "The last unit was just reserved by someone else.",
        "Try another offer with /browse"
    ),
    "invalid_input": lambda field, requirement: format_error_message(
        "❌",
        f"Invalid {field}.",
        f"{requirement}. Please try again."
    ),
}
