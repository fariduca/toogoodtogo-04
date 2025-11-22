"""Expiration job service.

Background job that periodically marks expired offers.
Runs on a schedule and updates offer status from ACTIVE to EXPIRED.
"""

from datetime import datetime

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository

logger = get_logger(__name__)


class ExpirationJob:
    """Background job to expire offers past their end time."""

    def __init__(self, offer_repo: PostgresOfferRepository):
        """
        Initialize expiration job.

        Args:
            offer_repo: Offer repository for querying and updating offers
        """
        self.offer_repo = offer_repo

    async def run(self) -> dict[str, int]:
        """
        Execute expiration job.

        Queries for offers past their end time and updates status to EXPIRED.

        Returns:
            Dictionary with counts: {"expired": count, "failed": count}
        """
        logger.info("expiration_job_started")

        try:
            # Get offers that have passed their end time
            expired_offers = await self.offer_repo.get_expired_offers()

            expired_count = 0
            failed_count = 0

            for offer in expired_offers:
                try:
                    # Update status to EXPIRED
                    await self.offer_repo.update_status(offer.id, OfferStatus.EXPIRED)
                    expired_count += 1

                    logger.info(
                        "offer_expired",
                        offer_id=str(offer.id),
                        business_id=str(offer.business_id),
                        end_time=offer.end_time.isoformat(),
                    )

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        "offer_expiration_failed",
                        offer_id=str(offer.id),
                        error=str(e),
                        exc_info=True,
                    )

            result = {"expired": expired_count, "failed": failed_count}

            logger.info(
                "expiration_job_completed",
                expired=expired_count,
                failed=failed_count,
            )

            return result

        except Exception as e:
            logger.error("expiration_job_error", error=str(e), exc_info=True)
            return {"expired": 0, "failed": 0}

    async def run_once(self) -> dict[str, int]:
        """
        Run expiration job once (for manual trigger or testing).

        Returns:
            Dictionary with counts: {"expired": count, "failed": count}
        """
        return await self.run()
