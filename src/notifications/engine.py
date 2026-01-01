"""Notification engine."""

from typing import Dict, List
from datetime import datetime

from ..models.event import StructuredEvent
from ..models.notification import Notification, NotificationStatus
from .channel import NotificationChannel


class NotificationEngine:
    """Main notification engine."""
    
    def __init__(self, channels: Dict[str, NotificationChannel]):
        """Initialize notification engine with channels."""
        self.channels = channels
    
    async def send_notification(
        self,
        event: StructuredEvent,
        channel: str,
        recipient: str,
        message: str = None
    ) -> Notification:
        """Send notification for an event."""
        # Get channel
        if channel not in self.channels:
            raise ValueError(f"Channel {channel} not available")
        
        channel_handler = self.channels[channel]
        
        # Validate recipient
        if not await channel_handler.validate_recipient(recipient):
            raise ValueError(f"Invalid recipient format for {channel}")
        
        # Create notification
        notification = Notification(
            notification_id=f"notif_{datetime.now().timestamp()}",
            event_id=event.event_id,
            channel=channel,
            recipient=recipient,
            message=message or self._generate_message(event),
            status=NotificationStatus.PENDING
        )
        
        # Send via channel
        try:
            success = await channel_handler.send(notification)
            if success:
                notification.status = NotificationStatus.SENT
                notification.delivery_timestamp = datetime.now()
            else:
                notification.status = NotificationStatus.FAILED
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
        
        return notification
    
    async def send_to_multiple_channels(
        self,
        event: StructuredEvent,
        recipients: Dict[str, List[str]],
        message: str = None
    ) -> List[Notification]:
        """Send notifications to multiple channels and recipients."""
        notifications = []
        for channel, channel_recipients in recipients.items():
            for recipient in channel_recipients:
                try:
                    notification = await self.send_notification(
                        event, channel, recipient, message
                    )
                    notifications.append(notification)
                except Exception as e:
                    # TODO: Log error
                    print(f"Failed to send {channel} notification: {e}")
        
        return notifications
    
    def _generate_message(self, event: StructuredEvent) -> str:
        """Generate default notification message from event."""
        message = f"Event: {event.title}"
        if event.due_date:
            message += f"\nDue: {event.due_date}"
        if event.description:
            message += f"\n{event.description}"
        return message


