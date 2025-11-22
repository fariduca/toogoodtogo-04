"""Permission checks for bot commands."""

from enum import Enum
from uuid import UUID

from src.models.business import Business, VerificationStatus


class Permission(str, Enum):
    """Permission types."""

    POST_OFFER = "post_offer"
    EDIT_OFFER = "edit_offer"
    APPROVE_BUSINESS = "approve_business"
    VIEW_OFFERS = "view_offers"
    PURCHASE = "purchase"


class PermissionChecker:
    """Check user permissions for actions."""

    def __init__(self, admin_user_ids: list[int] | None = None):
        """Initialize permission checker."""
        self.admin_user_ids = admin_user_ids or []

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in self.admin_user_ids

    def can_post_offer(self, business: Business) -> bool:
        """Check if business can post offers."""
        return business.verification_status == VerificationStatus.APPROVED

    def can_edit_offer(self, business: Business, offer_business_id: UUID) -> bool:
        """Check if business can edit offer."""
        return (
            business.verification_status == VerificationStatus.APPROVED
            and business.id == offer_business_id
        )

    def can_approve_business(self, user_id: int) -> bool:
        """Check if user can approve businesses (admin only)."""
        return self.is_admin(user_id)

    def can_purchase(self, user_id: int) -> bool:
        """Check if user can make purchases (all users)."""
        return user_id > 0  # Basic validation
