"""Event queue interface and implementation."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from ..models.event import RawEvent


class EventQueue(ABC):
    """Abstract event queue interface."""
    
    @abstractmethod
    async def publish(self, event: RawEvent) -> bool:
        """Publish event to queue."""
        pass
    
    @abstractmethod
    async def consume(self) -> AsyncIterator[RawEvent]:
        """Consume events from queue."""
        pass
    
    @abstractmethod
    async def ack(self, event_id: str) -> bool:
        """Acknowledge event processing."""
        pass
    
    @abstractmethod
    async def nack(self, event_id: str, requeue: bool = True) -> bool:
        """Negative acknowledge event (failed processing)."""
        pass


class InMemoryEventQueue(EventQueue):
    """In-memory event queue (for development/testing)."""
    
    def __init__(self):
        """Initialize in-memory queue."""
        self.queue = []
        self.processing = {}
    
    async def publish(self, event: RawEvent) -> bool:
        """Publish event to queue."""
        self.queue.append(event)
        return True
    
    async def consume(self) -> AsyncIterator[RawEvent]:
        """Consume events from queue."""
        while True:
            if self.queue:
                event = self.queue.pop(0)
                self.processing[event.event_id] = event
                yield event
            else:
                # TODO: Implement proper async waiting
                break
    
    async def ack(self, event_id: str) -> bool:
        """Acknowledge event processing."""
        if event_id in self.processing:
            del self.processing[event_id]
        return True
    
    async def nack(self, event_id: str, requeue: bool = True) -> bool:
        """Negative acknowledge event."""
        if event_id in self.processing:
            event = self.processing.pop(event_id)
            if requeue:
                self.queue.append(event)
        return True

