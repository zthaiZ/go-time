"""Directions and travel time utilities for GoTime."""

from typing import Tuple, Optional
import logging
from .client import GoogleMapsClient


logger = logging.getLogger(__name__)


class DirectionsService:
    """Service for directions and travel time operations."""
    
    def __init__(self, client: Optional[GoogleMapsClient] = None):
        """Initialize directions service.
        
        Args:
            client: Google Maps client. If None, creates new client.
        """
        self.client = client or GoogleMapsClient()
    
    def get_current_travel_time(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float]
    ) -> Optional[int]:
        """Get current travel time between two points.
        
        Args:
            origin: (latitude, longitude) of start point
            destination: (latitude, longitude) of end point
            
        Returns:
            Travel time in seconds or None if calculation fails
        """
        try:
            return self.client.get_travel_time(origin, destination, "now")
        except Exception as e:
            logger.error(f"Failed to get travel time: {e}")
            return None
    
    def format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string (e.g., "1h 23m", "45m", "2m")
        """
        if seconds < 60:
            return f"{seconds}s"
        
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours}h"
        
        return f"{hours}h {remaining_minutes}m"