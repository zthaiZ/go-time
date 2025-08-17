"""Geocoding utilities for GoTime."""

from typing import Optional, Tuple
import logging
from .client import GoogleMapsClient


logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for address geocoding operations."""
    
    def __init__(self, client: Optional[GoogleMapsClient] = None):
        """Initialize geocoding service.
        
        Args:
            client: Google Maps client. If None, creates new client.
        """
        self.client = client or GoogleMapsClient()
    
    def validate_and_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Validate and geocode an address.
        
        Args:
            address: Address string to validate and geocode
            
        Returns:
            Tuple of (latitude, longitude) or None if invalid
        """
        if not address or not address.strip():
            logger.warning("Empty address provided for geocoding")
            return None
            
        address = address.strip()
        try:
            return self.client.geocode(address)
        except Exception as e:
            logger.error(f"Failed to geocode address '{address}': {e}")
            return None
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """Convert coordinates back to address.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Formatted address string or None if reverse geocoding fails
        """
        # Note: This would use client.reverse_geocode() when implemented
        # For now, just return coordinate string
        return f"{lat}, {lng}"