"""Discovery ranking service for offers."""

from uuid import UUID

from src.models.offer import Offer


class DiscoveryRankingService:
    """Service for ranking offers in discovery view."""

    def __init__(self):
        """Initialize discovery ranking service."""
        pass

    async def rank_offers(
        self,
        offers: list[Offer],
        user_id: int | None = None,
        user_location: tuple[float, float] | None = None,
    ) -> list[Offer]:
        """Rank offers for discovery.

        MVP strategy: Latest + simple popularity (purchase count).
        Future: Add geo proximity, category weighting.
        """
        # For MVP, sort by created_at (latest first)
        # TODO: Add popularity score from purchase count
        # TODO: Add geo proximity weighting when coordinates available
        return sorted(offers, key=lambda o: o.created_at, reverse=True)

    async def get_popularity_score(self, offer_id: UUID) -> int:
        """Get popularity score (purchase count) for offer."""
        # TODO: Query purchase repository for confirmed purchase count
        return 0

    async def calculate_distance(
        self,
        location1: tuple[float, float],
        location2: tuple[float, float],
    ) -> float:
        """Calculate distance between two coordinates (km)."""
        # TODO: Implement haversine formula for geo distance
        return 0.0
