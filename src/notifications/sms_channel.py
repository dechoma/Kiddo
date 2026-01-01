"""SMS notification channel."""

from .channel import NotificationChannel
from ..models.notification import Notification


class SMSChannel(NotificationChannel):
    """SMS notification channel."""
    
    def __init__(self, config: dict):
        """Initialize SMS channel."""
        super().__init__("sms", config)
        # TODO: Initialize SMS gateway client
    
    async def send(self, notification: Notification) -> bool:
        """Send SMS notification."""
        # TODO: Implement SMS sending via gateway
        # Handle rate limiting
        # Handle delivery receipts
        return True
    
    async def check_delivery_status(self, notification: Notification) -> str:
        """Check SMS delivery status."""
        # TODO: Implement status check
        return notification.status.value
    
    async def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format."""
        # TODO: Implement phone number validation
        # Basic check: should be digits, optionally with + prefix
        return recipient.replace("+", "").replace("-", "").replace(" ", "").isdigit()


