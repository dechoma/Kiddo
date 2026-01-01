"""Data extraction and validation."""

from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from ..models.event import StructuredEvent


class DataExtractor:
    """Extract and validate structured data from LLM results."""
    
    async def extract(
        self,
        normalized_event: Dict[str, Any],
        llm_result: Dict[str, Any]
    ) -> StructuredEvent:
        """
        Extract structured event from normalized event and LLM result.
        
        Validates and enriches the extracted data.
        """
        # Generate unique event ID
        event_id = str(uuid.uuid4())
        
        # Parse dates
        due_date = self._parse_datetime(llm_result.get("due_date"))
        start_time = self._parse_datetime(llm_result.get("start_time"))
        end_time = self._parse_datetime(llm_result.get("end_time"))
        
        # Parse alert_before_minutes
        alert_before = llm_result.get("alert_before_minutes")
        if alert_before is not None:
            try:
                alert_before = int(alert_before)
            except (ValueError, TypeError):
                alert_before = None
        
        # Build structured event
        structured = StructuredEvent(
            event_id=event_id,
            event_type=llm_result.get("event_type", "unknown"),
            title=llm_result.get("title", "Untitled Event"),
            description=llm_result.get("description"),
            due_date=due_date,
            start_time=start_time,
            end_time=end_time,
            participants=llm_result.get("participants", []),
            location=llm_result.get("location"),
            priority=llm_result.get("priority"),
            source_reference=normalized_event.get("source_id"),
            alert_before_minutes=alert_before,
            is_recurring=llm_result.get("is_recurring", False),
            recurrence_pattern=llm_result.get("recurrence_pattern"),
            metadata={
                "llm_extracted": True,
                "extraction_timestamp": datetime.now().isoformat(),
                **normalized_event.get("metadata", {})
            }
        )
        
        # Validate
        self._validate(structured)
        
        return structured
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if value is None:
            return None
        
        # TODO: Implement robust datetime parsing
        # Handle ISO format, relative dates, etc.
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                # TODO: Try other formats
                pass
        
        return None
    
    def _validate(self, event: StructuredEvent) -> None:
        """Validate structured event data."""
        # TODO: Implement validation rules
        # - Required fields
        # - Date consistency (start < end)
        # - Format validation
        if not event.title:
            raise ValueError("Event title is required")
        
        if event.start_time and event.end_time:
            if event.start_time >= event.end_time:
                raise ValueError("Start time must be before end time")

