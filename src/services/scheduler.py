"""Scheduler for background tasks (offer expiration)."""

import asyncio
from datetime import datetime

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository

logger = get_logger(__name__)


class SchedulerService:
    """Background task scheduler for offer lifecycle."""

    def __init__(self, offer_repo: PostgresOfferRepository, interval_seconds: int = 60):
        """Initialize scheduler service."""
        self.offer_repo = offer_repo
        self.interval_seconds = interval_seconds
        self._running = False

    async def start(self) -> None:
        """Start scheduler loop."""
        self._running = True
        logger.info("Scheduler started", interval_seconds=self.interval_seconds)

        while self._running:
            try:
                await self.expire_offers()
                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                logger.error("Scheduler error", error=str(e))
                await asyncio.sleep(self.interval_seconds)

    async def stop(self) -> None:
        """Stop scheduler loop."""
        self._running = False
        logger.info("Scheduler stopped")

    async def expire_offers(self) -> None:
        """Mark expired offers as EXPIRED."""
        try:
            expired = await self.offer_repo.get_expired_offers()
            for offer in expired:
                await self.offer_repo.update_status(offer.id, OfferStatus.EXPIRED)
                logger.info("Offer expired", offer_id=str(offer.id), title=offer.title)

            if expired:
                logger.info("Expired offers processed", count=len(expired))
        except Exception as e:
            logger.error("Failed to expire offers", error=str(e))
