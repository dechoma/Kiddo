"""Calendar provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.event import StructuredEvent
from ..models.calendar import CalendarEvent, SyncStatus


class CalendarProvider(ABC):
    """Abstract interface for calendar providers."""
    
    def __init__(self, provider_name: str, config: dict):
        """Initialize calendar provider."""
        self.provider_name = provider_name
        self.config = config
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with calendar provider."""
        pass
    
    @abstractmethod
    async def create_event(
        self,
        structured_event: StructuredEvent,
        calendar_id: str
    ) -> CalendarEvent:
        """Create event in calendar."""
        pass
    
    @abstractmethod
    async def update_event(
        self,
        calendar_event: CalendarEvent,
        structured_event: StructuredEvent
    ) -> CalendarEvent:
        """Update existing calendar event."""
        pass
    
    @abstractmethod
    async def delete_event(self, calendar_event: CalendarEvent) -> bool:
        """Delete event from calendar."""
        pass
    
    @abstractmethod
    async def list_calendars(self) -> List[str]:
        """List available calendars."""
        pass
    
    @abstractmethod
    async def sync_status(self, calendar_event: CalendarEvent) -> SyncStatus:
        """Check sync status of calendar event."""
        pass


