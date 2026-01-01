"""Notification channel interface."""

from abc import ABC, abstractmethod

from ..models.notification import Notification


class NotificationChannel(ABC):
    """Abstract interface for notification channels."""
    
    def __init__(self, channel_name: str, config: dict):
        """Initialize notification channel."""
        self.channel_name = channel_name
        self.config = config
    
    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send notification via this channel."""
        pass
    
    @abstractmethod
    async def check_delivery_status(self, notification: Notification) -> str:
        """Check delivery status of notification."""
        pass
    
    @abstractmethod
    async def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient format for this channel."""
        pass


