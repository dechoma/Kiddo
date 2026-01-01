"""Event data models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RawEvent:
    """Raw event from source."""
    source_id: str
    timestamp: datetime
    raw_payload: Dict[str, Any]
    source_metadata: Dict[str, Any]
    event_id: Optional[str] = None


@dataclass
class StructuredEvent:
    """Structured event after processing."""
    event_id: str
    event_type: str
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    participants: List[str] = None
    location: Optional[str] = None
    priority: Optional[str] = None
    source_reference: Optional[str] = None
    metadata: Dict[str, Any] = None
    alert_before_minutes: Optional[int] = None  # Minutes before event for alert/reminder
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # e.g., "daily", "weekly", "monthly"
    
    def __post_init__(self):
        if self.participants is None:
            self.participants = []
        if self.metadata is None:
            self.metadata = {}
        # Default alert if not specified (2 minutes before)
        if self.alert_before_minutes is None:
            self.alert_before_minutes = 15

