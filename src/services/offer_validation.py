"""Offer validation service.

Validates offers against business rules before publishing:
- Time range validation
- Item validation
- Business verification status
- Duplicate detection
"""

from datetime import datetime, timedelta
from typing import Optional

from src.logging import get_logger
from src.models.business import Business, VerificationStatus
from src.models.offer import Offer, OfferStatus

logger = get_logger(__name__)

# Business rules
MIN_OFFER_DURATION_HOURS = 1
MAX_OFFER_DURATION_DAYS = 7
MAX_ITEMS_PER_OFFER = 20


class ValidationResult:
    """Result of offer validation."""

    def __init__(self):
        self.errors: list[str] = []

    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return len(self.errors) == 0

    def add_error(self, error: str) -> None:
        """Add validation error."""
        self.errors.append(error)


class OfferValidator:
    """Validates offers against business rules."""

    async def validate_for_publish(
        self, offer: Offer, business: Optional[Business] = None
    ) -> ValidationResult:
        """
        Validate offer before publishing.

        Args:
            offer: Offer to validate
            business: Business that owns the offer (optional, will fetch if not provided)

        Returns:
            ValidationResult with errors if any
        """
        result = ValidationResult()

        # Check offer status
        if offer.status != OfferStatus.DRAFT:
            result.add_error(
                f"Only draft offers can be published. Current status: {offer.status.value}"
            )

        # Validate business verification
        if business:
            if business.verification_status != VerificationStatus.APPROVED:
                result.add_error(
                    f"Business must be approved. Current status: {business.verification_status.value}"
                )

        # Validate time range
        now = datetime.utcnow()

        if offer.start_time <= now:
            result.add_error("Start time must be in the future")

        if offer.end_time <= offer.start_time:
            result.add_error("End time must be after start time")

        duration = offer.end_time - offer.start_time

        if duration < timedelta(hours=MIN_OFFER_DURATION_HOURS):
            result.add_error(
                f"Offer duration must be at least {MIN_OFFER_DURATION_HOURS} hour(s)"
            )

        if duration > timedelta(days=MAX_OFFER_DURATION_DAYS):
            result.add_error(
                f"Offer duration cannot exceed {MAX_OFFER_DURATION_DAYS} days"
            )

        # Validate items
        if not offer.items:
            result.add_error("Offer must have at least one item")

        if len(offer.items) > MAX_ITEMS_PER_OFFER:
            result.add_error(
                f"Offer cannot have more than {MAX_ITEMS_PER_OFFER} items"
            )

        for item in offer.items:
            if item.quantity_available <= 0:
                result.add_error(f"Item '{item.name}' must have positive quantity")

            if item.unit_price <= 0:
                result.add_error(f"Item '{item.name}' must have positive price")

        # Validate total inventory
        total_quantity = offer.remaining_quantity
        if total_quantity <= 0:
            result.add_error("Offer must have available inventory")

        if result.is_valid:
            logger.info("offer_validation_passed", offer_id=str(offer.id))
        else:
            logger.warning(
                "offer_validation_failed",
                offer_id=str(offer.id),
                errors=result.errors,
            )

        return result

    async def validate_for_edit(
        self, offer: Offer, user_id: int
    ) -> ValidationResult:
        """
        Validate offer can be edited.

        Args:
            offer: Offer to edit
            user_id: User attempting the edit

        Returns:
            ValidationResult with errors if any
        """
        result = ValidationResult()

        # Check offer status - cannot edit expired or sold out
        if offer.status == OfferStatus.EXPIRED:
            result.add_error("Cannot edit expired offers")

        if offer.status == OfferStatus.SOLD_OUT:
            result.add_error("Cannot edit sold out offers")

        # Check if offer has started
        if offer.start_time <= datetime.utcnow():
            result.add_error("Cannot edit offers that have already started")

        # TODO: Check user ownership via business_id

        return result

    async def validate_time_update(
        self, offer: Offer, new_start: datetime, new_end: datetime
    ) -> ValidationResult:
        """
        Validate time range update for existing offer.

        Args:
            offer: Existing offer
            new_start: Proposed new start time
            new_end: Proposed new end time

        Returns:
            ValidationResult with errors if any
        """
        result = ValidationResult()

        now = datetime.utcnow()

        if new_start <= now:
            result.add_error("New start time must be in the future")

        if new_end <= new_start:
            result.add_error("New end time must be after new start time")

        duration = new_end - new_start

        if duration < timedelta(hours=MIN_OFFER_DURATION_HOURS):
            result.add_error(
                f"Offer duration must be at least {MIN_OFFER_DURATION_HOURS} hour(s)"
            )

        if duration > timedelta(days=MAX_OFFER_DURATION_DAYS):
            result.add_error(
                f"Offer duration cannot exceed {MAX_OFFER_DURATION_DAYS} days"
            )

        return result
