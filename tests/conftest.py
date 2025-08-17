"""Test configuration and fixtures."""

import sys
from unittest.mock import MagicMock

# Mock googlemaps module for testing without API
mock_googlemaps = MagicMock()
mock_googlemaps.Client = MagicMock
mock_googlemaps.exceptions = MagicMock()
mock_googlemaps.exceptions.ApiError = Exception
mock_googlemaps.exceptions.Timeout = Exception  
mock_googlemaps.exceptions.TransportError = Exception

sys.modules['googlemaps'] = mock_googlemaps
sys.modules['googlemaps.exceptions'] = mock_googlemaps.exceptions