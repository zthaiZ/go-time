"""Google Maps API client for GoTime."""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError
from .config import get_settings


logger = logging.getLogger(__name__)


class GoogleMapsClient:
    """Client for interacting with Google Maps APIs with built-in rate limiting."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Google Maps client with rate limiting.
        
        Args:
            api_key: Google Maps API key. If None, loads from settings.
        """
        settings = get_settings()
        if api_key is None:
            api_key = settings.google_maps_api_key
            
        self._client = googlemaps.Client(key=api_key)
        
        # Rate limiting setup
        self._requests_per_minute = settings.api_requests_per_minute
        self._requests_per_day = settings.api_requests_per_day
        
        # Track requests for rate limiting
        self._minute_requests = deque()
        self._daily_requests = 0
        self._daily_reset_time = datetime.now() + timedelta(days=1)
        
        logger.info(f"Google Maps client initialized with rate limits: {self._requests_per_minute}/min, {self._requests_per_day}/day")
    
    def _check_rate_limits(self) -> bool:
        """Check if we're within rate limits before making a request.
        
        Returns:
            True if request can proceed, False if rate limited
        """
        now = datetime.now()
        
        # Reset daily counter if needed
        if now >= self._daily_reset_time:
            self._daily_requests = 0
            self._daily_reset_time = now + timedelta(days=1)
            logger.info("Daily API request counter reset")
        
        # Check daily limit
        if self._daily_requests >= self._requests_per_day:
            logger.warning(f"Daily API request limit reached ({self._requests_per_day})")
            return False
        
        # Clean old minute requests (older than 60 seconds)
        minute_ago = now - timedelta(seconds=60)
        while self._minute_requests and self._minute_requests[0] < minute_ago:
            self._minute_requests.popleft()
        
        # Check minute limit
        if len(self._minute_requests) >= self._requests_per_minute:
            logger.warning(f"Per-minute API request limit reached ({self._requests_per_minute})")
            return False
        
        return True
    
    def _record_request(self) -> None:
        """Record that an API request was made."""
        now = datetime.now()
        self._minute_requests.append(now)
        self._daily_requests += 1
        logger.debug(f"API request recorded. Daily: {self._daily_requests}/{self._requests_per_day}, Minute: {len(self._minute_requests)}/{self._requests_per_minute}")
    
    def _wait_for_rate_limit(self) -> None:
        """Wait until we can make another request without exceeding rate limits."""
        while not self._check_rate_limits():
            # If we're at the minute limit, wait until the oldest request is > 60 seconds old
            if self._minute_requests:
                oldest_request = self._minute_requests[0]
                wait_until = oldest_request + timedelta(seconds=61)  # +1 second buffer
                wait_time = (wait_until - datetime.now()).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                    time.sleep(min(wait_time, 10))  # Wait max 10 seconds at a time
            else:
                # Daily limit reached, wait longer
                logger.info("Daily rate limit reached, waiting 60 seconds")
                time.sleep(60)
    
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
        # Rate limiting check
        self._wait_for_rate_limit()
        
        try:
            self._record_request()
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
        # Rate limiting check
        self._wait_for_rate_limit()
        
        try:
            self._record_request()
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
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current API usage statistics.
        
        Returns:
            Dictionary with usage stats
        """
        now = datetime.now()
        
        # Clean old minute requests
        minute_ago = now - timedelta(seconds=60)
        while self._minute_requests and self._minute_requests[0] < minute_ago:
            self._minute_requests.popleft()
        
        return {
            "daily_requests": self._daily_requests,
            "daily_limit": self._requests_per_day,
            "daily_remaining": self._requests_per_day - self._daily_requests,
            "minute_requests": len(self._minute_requests),
            "minute_limit": self._requests_per_minute,
            "minute_remaining": self._requests_per_minute - len(self._minute_requests),
            "daily_reset_time": self._daily_reset_time.isoformat()
        }