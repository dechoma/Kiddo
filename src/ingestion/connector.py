"""Source connector interface."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional

from ..models.event import RawEvent


class SourceConnector(ABC):
    """Abstract interface for event source connectors."""
    
    def __init__(self, source_id: str, config: dict):
        """Initialize connector with source ID and configuration."""
        self.source_id = source_id
        self.config = config
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to event source."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to event source."""
        pass
    
    @abstractmethod
    async def fetch_events(self) -> AsyncIterator[RawEvent]:
        """Fetch events from source."""
        yield
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if source is healthy and accessible."""
        pass
    
    async def mark_as_processed(self, event: RawEvent) -> bool:
        """
        Mark an event as processed.
        
        Override this method to implement connector-specific tracking.
        Default implementation does nothing and returns True.
        
        Args:
            event: The event to mark as processed
            
        Returns:
            True if successfully marked, False otherwise
        """
        return True

