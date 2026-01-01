"""Notification models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


@dataclass
class Notification:
    """Notification representation."""
    notification_id: str
    event_id: str
    channel: str
    recipient: str
    message: str
    status: NotificationStatus = NotificationStatus.PENDING
    delivery_timestamp: Optional[datetime] = None
    error_message: Optional[str] = None


