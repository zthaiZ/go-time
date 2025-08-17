"""Google Maps API client for GoTime."""

import logging
from typing import Dict, Any, Optional, Tuple
import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError
from .config import get_settings


logger = logging.getLogger(__name__)


class GoogleMapsClient:
    """Client for interacting with Google Maps APIs."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Google Maps client.
        
        Args:
            api_key: Google Maps API key. If None, loads from settings.
        """
        if api_key is None:
            api_key = get_settings().google_maps_api_key
            
        self._client = googlemaps.Client(key=api_key)
        logger.info("Google Maps client initialized")
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to latitude/longitude coordinates.
        
        Args:
            address: Address string to geocode
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
            
        Raises:
            ApiError: For API-related errors
            ValueError: For invalid address format
        """
        try:
            result = self._client.geocode(address)
            if not result:
                logger.warning(f"No geocoding results for address: {address}")
                return None
                
            location = result[0]['geometry']['location']
            coords = (location['lat'], location['lng'])
            logger.info(f"Geocoded '{address}' to {coords}")
            return coords
            
        except (ApiError, Timeout, TransportError) as e:
            logger.error(f"Google Maps API error during geocoding: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during geocoding: {e}")
            raise ValueError(f"Invalid address format: {address}") from e
    
    def get_travel_time(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float],
        departure_time: str = "now"
    ) -> Optional[int]:
        """Get travel time in seconds between two points.
        
        Args:
            origin: (latitude, longitude) of start point
            destination: (latitude, longitude) of end point  
            departure_time: When to calculate for ("now" or timestamp)
            
        Returns:
            Travel time in seconds or None if calculation fails
            
        Raises:
            ApiError: For API-related errors
        """
        try:
            result = self._client.directions(
                origin=origin,
                destination=destination,
                mode="driving",
                departure_time=departure_time,
                traffic_model="best_guess"
            )
            
            if not result:
                logger.warning(f"No route found from {origin} to {destination}")
                return None
                
            duration = result[0]['legs'][0]['duration_in_traffic']['value']
            logger.info(f"Travel time from {origin} to {destination}: {duration}s")
            return duration
            
        except (ApiError, Timeout, TransportError) as e:
            logger.error(f"Google Maps API error during travel time calculation: {e}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during travel time calculation: {e}")
            raise