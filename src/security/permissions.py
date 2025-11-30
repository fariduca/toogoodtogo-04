"""Permission checks for bot commands."""

from enum import Enum
from uuid import UUID

from src.models.business import Business, VerificationStatus
from src.models.user import User, UserRole


class Permission(str, Enum):
    """Permission types."""

    POST_OFFER = "post_offer"
    EDIT_OFFER = "edit_offer"
    APPROVE_BUSINESS = "approve_business"
    VIEW_OFFERS = "view_offers"
    MAKE_RESERVATION = "make_reservation"


class PermissionChecker:
    """Check user permissions for actions."""

    def __init__(self, admin_user_ids: list[int] | None = None):
        """Initialize permission checker."""
        self.admin_user_ids = admin_user_ids or []

    def is_admin(self, telegram_user_id: int) -> bool:
        """Check if user is admin by telegram ID."""
        return telegram_user_id in self.admin_user_ids

    def can_post_offer(self, user: User, business: Business) -> bool:
        """Check if user can post offers."""
        return (
            user.role == UserRole.BUSINESS
            and business.owner_id == user.id
            and business.verification_status == VerificationStatus.APPROVED
        )

    def can_edit_offer(self, user: User, business: Business, offer_business_id: UUID) -> bool:
        """Check if user can edit offer."""
        return (
            user.role == UserRole.BUSINESS
            and business.owner_id == user.id
            and business.verification_status == VerificationStatus.APPROVED
            and business.id == offer_business_id
        )

    def can_approve_business(self, telegram_user_id: int) -> bool:
        """Check if user can approve businesses (admin only)."""
        return self.is_admin(telegram_user_id)

    def can_make_reservation(self, user: User) -> bool:
        """Check if user can make reservations (customers only)."""
        return user.role == UserRole.CUSTOMER
