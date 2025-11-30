"""Discovery ranking service with geolocation filtering."""

import math
from typing import Optional

from src.models.offer import Offer


class DiscoveryRankingService:
    """Service for ranking and filtering offers based on geolocation."""

    def __init__(self, nearby_radius_km: float = 5.0):
        """Initialize discovery ranking service."""
        self.nearby_radius_km = nearby_radius_km

    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two coordinates using Haversine formula.
        
        Returns distance in kilometers.
        """
        # Earth's radius in kilometers
        R = 6371.0

        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    def is_within_radius(
        self,
        user_lat: float,
        user_lon: float,
        business_lat: float,
        business_lon: float,
        radius_km: Optional[float] = None,
    ) -> bool:
        """Check if business is within specified radius of user."""
        radius = radius_km if radius_km is not None else self.nearby_radius_km
        distance = self.calculate_distance(user_lat, user_lon, business_lat, business_lon)
        return distance <= radius

    def filter_offers_by_location(
        self,
        offers: list[tuple[Offer, float, float]],  # (offer, business_lat, business_lon)
        user_lat: float,
        user_lon: float,
    ) -> list[tuple[Offer, float]]:  # (offer, distance_km)
        """Filter offers by proximity and return with distances."""
        results = []
        for offer, business_lat, business_lon in offers:
            distance = self.calculate_distance(
                user_lat, user_lon, business_lat, business_lon
            )
            if distance <= self.nearby_radius_km:
                results.append((offer, distance))

        # Sort by distance (closest first)
        results.sort(key=lambda x: x[1])
        return results

    def rank_offers(
        self,
        offers: list[tuple[Offer, float]],  # (offer, distance_km)
    ) -> list[Offer]:
        """Rank offers by distance and recency."""
        # For MVP, simple ranking: closest first, then most recent
        # Already sorted by distance from filter_offers_by_location
        return [offer for offer, _ in offers]
