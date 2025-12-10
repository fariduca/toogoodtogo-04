"""Structured audit logging for critical business actions.

Provides detailed audit trails for compliance and security monitoring.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from src.logging import get_logger

logger = get_logger(__name__)


class AuditEventType(str, Enum):
    """Types of auditable events."""

    # Business management
    BUSINESS_REGISTERED = "business_registered"
    BUSINESS_VERIFIED = "business_verified"
    BUSINESS_REJECTED = "business_rejected"

    # Offer lifecycle
    OFFER_CREATED = "offer_created"
    OFFER_PUBLISHED = "offer_published"
    OFFER_PAUSED = "offer_paused"
    OFFER_RESUMED = "offer_resumed"
    OFFER_EDITED = "offer_edited"
    OFFER_SOLD_OUT = "offer_sold_out"
    OFFER_EXPIRED = "offer_expired"

    # Purchase flow
    PURCHASE_INITIATED = "purchase_initiated"
    PURCHASE_CONFIRMED = "purchase_confirmed"
    PURCHASE_CANCELED = "purchase_canceled"
    PURCHASE_FAILED = "purchase_failed"

    # Security
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_ACCESS_ATTEMPT = "invalid_access_attempt"


class AuditLogger:
    """Centralized audit logging service."""

    @staticmethod
    def log_event(
        event_type: AuditEventType,
        actor_id: int,
        resource_type: str,
        resource_id: UUID | str,
        action: str,
        success: bool = True,
        metadata: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Log an auditable event with structured context.

        Args:
            event_type: Type of audit event
            actor_id: Telegram user ID performing the action
            resource_type: Type of resource (business, offer, purchase)
            resource_id: ID of the affected resource
            action: Human-readable action description
            success: Whether the action succeeded
            metadata: Additional context (prices, quantities, etc.)
            error: Error message if action failed
        """
        audit_entry = {
            "event_type": event_type.value,
            "actor_id": actor_id,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "action": action,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        if error:
            audit_entry["error"] = error

        logger.info(
            "audit_event",
            **audit_entry,
        )

    @staticmethod
    def log_business_registered(
        actor_id: int,
        business_id: UUID,
        business_name: str,
        venue_address: str,
    ) -> None:
        """Log business registration."""
        AuditLogger.log_event(
            event_type=AuditEventType.BUSINESS_REGISTERED,
            actor_id=actor_id,
            resource_type="business",
            resource_id=business_id,
            action=f"Registered business: {business_name}",
            metadata={
                "business_name": business_name,
                "venue_address": venue_address,
            },
        )

    @staticmethod
    def log_business_verified(
        actor_id: int,
        business_id: UUID,
        business_name: str,
        approved: bool,
    ) -> None:
        """Log business verification decision."""
        event_type = (
            AuditEventType.BUSINESS_VERIFIED
            if approved
            else AuditEventType.BUSINESS_REJECTED
        )
        action = f"{'Approved' if approved else 'Rejected'} business: {business_name}"

        AuditLogger.log_event(
            event_type=event_type,
            actor_id=actor_id,
            resource_type="business",
            resource_id=business_id,
            action=action,
            metadata={"business_name": business_name, "approved": approved},
        )

    @staticmethod
    def log_offer_published(
        actor_id: int,
        offer_id: UUID,
        offer_title: str,
        total_value: float,
    ) -> None:
        """Log offer publication."""
        AuditLogger.log_event(
            event_type=AuditEventType.OFFER_PUBLISHED,
            actor_id=actor_id,
            resource_type="offer",
            resource_id=offer_id,
            action=f"Published offer: {offer_title}",
            metadata={
                "offer_title": offer_title,
                "total_value": total_value,
            },
        )

    @staticmethod
    def log_offer_edited(
        actor_id: int,
        offer_id: UUID,
        offer_title: str,
        changes: dict[str, Any],
    ) -> None:
        """Log offer edits."""
        AuditLogger.log_event(
            event_type=AuditEventType.OFFER_EDITED,
            actor_id=actor_id,
            resource_type="offer",
            resource_id=offer_id,
            action=f"Edited offer: {offer_title}",
            metadata={
                "offer_title": offer_title,
                "changes": changes,
            },
        )

    @staticmethod
    def log_purchase_confirmed(
        actor_id: int,
        purchase_id: UUID,
        offer_id: UUID,
        amount: float,
        payment_method: str,
    ) -> None:
        """Log successful purchase."""
        AuditLogger.log_event(
            event_type=AuditEventType.PURCHASE_CONFIRMED,
            actor_id=actor_id,
            resource_type="purchase",
            resource_id=purchase_id,
            action="Purchase confirmed",
            metadata={
                "offer_id": str(offer_id),
                "amount": amount,
                "payment_method": payment_method,
            },
        )

    @staticmethod
    def log_purchase_canceled(
        actor_id: int,
        purchase_id: UUID,
        reason: str,
    ) -> None:
        """Log purchase cancellation."""
        AuditLogger.log_event(
            event_type=AuditEventType.PURCHASE_CANCELED,
            actor_id=actor_id,
            resource_type="purchase",
            resource_id=purchase_id,
            action="Purchase canceled",
            metadata={"reason": reason},
        )

    @staticmethod
    def log_permission_denied(
        actor_id: int,
        resource_type: str,
        resource_id: UUID | str,
        attempted_action: str,
    ) -> None:
        """Log unauthorized access attempts."""
        AuditLogger.log_event(
            event_type=AuditEventType.PERMISSION_DENIED,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=f"Permission denied: {attempted_action}",
            success=False,
            metadata={"attempted_action": attempted_action},
        )

    @staticmethod
    def log_rate_limit_exceeded(
        actor_id: int,
        action: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        """Log rate limit violations."""
        AuditLogger.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            actor_id=actor_id,
            resource_type="system",
            resource_id="rate_limiter",
            action=f"Rate limit exceeded: {action}",
            success=False,
            metadata={
                "action": action,
                "limit": limit,
                "window_seconds": window_seconds,
            },
        )
