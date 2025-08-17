"""Monitoring engine and session management for GoTime."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass
import uuid

from .client import GoogleMapsClient
from .directions import DirectionsService
from .config import get_settings


logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Monitoring session status."""
    PENDING = "pending"
    ACTIVE = "active"  
    TARGET_REACHED = "target_reached"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class MonitoringResult:
    """Result of a monitoring session."""
    session_id: str
    status: SessionStatus
    final_travel_time: Optional[int]
    target_duration: int
    message: str
    timestamp: datetime


class MonitoringSession:
    """Individual monitoring session for a route."""
    
    def __init__(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float], 
        target_duration_seconds: int,
        timeout_minutes: Optional[int] = None,
        polling_interval_seconds: Optional[int] = None
    ):
        """Initialize monitoring session.
        
        Args:
            origin: (latitude, longitude) of start point
            destination: (latitude, longitude) of end point
            target_duration_seconds: Target travel time in seconds
            timeout_minutes: Session timeout in minutes (None for default)
            polling_interval_seconds: Polling frequency (None for default)
        """
        self.session_id = str(uuid.uuid4())
        self.origin = origin
        self.destination = destination
        self.target_duration = target_duration_seconds
        self.status = SessionStatus.PENDING
        self.created_at = datetime.now()
        
        settings = get_settings()
        self.timeout_minutes = timeout_minutes or settings.default_timeout_minutes
        self.polling_interval = polling_interval_seconds or settings.polling_interval_seconds
        
        self.current_travel_time: Optional[int] = None
        self.last_check: Optional[datetime] = None
        self.error_message: Optional[str] = None
        
        logger.info(f"Created monitoring session {self.session_id}")
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == SessionStatus.ACTIVE
    
    @property
    def is_expired(self) -> bool:
        """Check if session has exceeded timeout."""
        if self.status != SessionStatus.ACTIVE:
            return False
        
        elapsed = datetime.now() - self.created_at
        return elapsed.total_seconds() > (self.timeout_minutes * 60)
    
    def start(self) -> None:
        """Start the monitoring session."""
        self.status = SessionStatus.ACTIVE
        logger.info(f"Started monitoring session {self.session_id}")
    
    def stop(self, status: SessionStatus, message: str) -> MonitoringResult:
        """Stop the monitoring session.
        
        Args:
            status: Final session status
            message: Result message
            
        Returns:
            MonitoringResult with session details
        """
        self.status = status
        result = MonitoringResult(
            session_id=self.session_id,
            status=status,
            final_travel_time=self.current_travel_time,
            target_duration=self.target_duration,
            message=message,
            timestamp=datetime.now()
        )
        
        logger.info(f"Stopped session {self.session_id}: {status.value} - {message}")
        return result


class MonitoringEngine:
    """Engine for managing and executing monitoring sessions."""
    
    def __init__(self, directions_service: Optional[DirectionsService] = None):
        """Initialize monitoring engine.
        
        Args:
            directions_service: Service for travel time calculations
        """
        self.directions_service = directions_service or DirectionsService()
        self.active_sessions: Dict[str, MonitoringSession] = {}
        self.notification_callback: Optional[Callable[[MonitoringResult], None]] = None
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info("Monitoring engine initialized")
    
    def set_notification_callback(self, callback: Callable[[MonitoringResult], None]) -> None:
        """Set callback function for notifications.
        
        Args:
            callback: Function to call when session completes
        """
        self.notification_callback = callback
        logger.info("Notification callback set")
    
    async def start_session(self, session: MonitoringSession) -> str:
        """Start monitoring a new session.
        
        Args:
            session: Session to monitor
            
        Returns:
            Session ID
            
        Raises:
            ValueError: If session is already active or engine is full
        """
        if session.session_id in self.active_sessions:
            raise ValueError(f"Session {session.session_id} already active")
        
        settings = get_settings()
        if len(self.active_sessions) >= settings.max_concurrent_sessions:
            raise ValueError("Maximum concurrent sessions reached")
        
        session.start()
        self.active_sessions[session.session_id] = session
        
        # Start monitoring loop if not already running
        if not self._running:
            await self._start_monitoring_loop()
        
        logger.info(f"Added session {session.session_id} to monitoring")
        return session.session_id
    
    async def stop_session(self, session_id: str) -> Optional[MonitoringResult]:
        """Stop a monitoring session.
        
        Args:
            session_id: ID of session to stop
            
        Returns:
            MonitoringResult if session existed, None otherwise
        """
        session = self.active_sessions.pop(session_id, None)
        if not session:
            return None
        
        result = session.stop(SessionStatus.CANCELLED, "Session cancelled by user")
        
        if self.notification_callback:
            self.notification_callback(result)
        
        return result
    
    async def _start_monitoring_loop(self) -> None:
        """Start the main monitoring loop."""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started monitoring loop")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that checks all active sessions."""
        while self._running and self.active_sessions:
            try:
                await self._check_all_sessions()
                await asyncio.sleep(10)  # Check every 10 seconds for session management
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error
        
        self._running = False
        logger.info("Monitoring loop stopped")
    
    async def _check_all_sessions(self) -> None:
        """Check all active sessions for updates."""
        completed_sessions = []
        
        for session_id, session in self.active_sessions.items():
            try:
                result = await self._check_session(session)
                if result:
                    completed_sessions.append(session_id)
                    if self.notification_callback:
                        self.notification_callback(result)
            except Exception as e:
                logger.error(f"Error checking session {session_id}: {e}")
                session.error_message = str(e)
                result = session.stop(SessionStatus.ERROR, f"Error: {e}")
                completed_sessions.append(session_id)
                if self.notification_callback:
                    self.notification_callback(result)
        
        # Remove completed sessions
        for session_id in completed_sessions:
            self.active_sessions.pop(session_id, None)
    
    async def _check_session(self, session: MonitoringSession) -> Optional[MonitoringResult]:
        """Check a single session for target reached or timeout.
        
        Args:
            session: Session to check
            
        Returns:
            MonitoringResult if session completed, None if still active
        """
        # Check if it's time to poll this session
        now = datetime.now()
        if (session.last_check and 
            (now - session.last_check).total_seconds() < session.polling_interval):
            return None
        
        # Check for timeout
        if session.is_expired:
            return session.stop(
                SessionStatus.TIMED_OUT, 
                f"Session timed out after {session.timeout_minutes} minutes"
            )
        
        # Get current travel time
        travel_time = self.directions_service.get_current_travel_time(
            session.origin, session.destination
        )
        
        if travel_time is None:
            logger.warning(f"Could not get travel time for session {session.session_id}")
            return None
        
        session.current_travel_time = travel_time
        session.last_check = now
        
        # Check if target reached
        if travel_time <= session.target_duration:
            duration_str = self.directions_service.format_duration(travel_time)
            target_str = self.directions_service.format_duration(session.target_duration)
            return session.stop(
                SessionStatus.TARGET_REACHED,
                f"Target reached! Current travel time: {duration_str} (target: {target_str})"
            )
        
        return None
    
    async def shutdown(self) -> None:
        """Shutdown the monitoring engine."""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop all active sessions
        for session in list(self.active_sessions.values()):
            session.stop(SessionStatus.CANCELLED, "Engine shutdown")
        
        self.active_sessions.clear()
        logger.info("Monitoring engine shutdown complete")