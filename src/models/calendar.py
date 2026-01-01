"""Calendar integration models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class SyncStatus(str, Enum):
    """Calendar sync status."""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"


@dataclass
class CalendarEvent:
    """Calendar event representation."""
    calendar_provider: str
    calendar_id: str
    provider_event_id: Optional[str] = None
    structured_event_id: str = None
    sync_status: SyncStatus = SyncStatus.PENDING
    last_sync_timestamp: Optional[datetime] = None
    error_message: Optional[str] = None


