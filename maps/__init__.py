"""GoTime Maps Package.

This package provides Google Maps integration for continuous monitoring
of travel times and route notifications.
"""

__version__ = "0.1.0"
__author__ = "GoTime Team"

from .client import GoogleMapsClient
from .monitoring import MonitoringSession, MonitoringEngine

__all__ = [
    "GoogleMapsClient",
    "MonitoringSession", 
    "MonitoringEngine"
]