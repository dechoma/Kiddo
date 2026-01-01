"""Event normalization."""

from typing import Dict, Any

from ..models.event import RawEvent


class EventNormalizer:
    """Normalize events from various sources to canonical format."""
    
    async def normalize(self, raw_event: RawEvent) -> Dict[str, Any]:
        """
        Normalize raw event to canonical format.
        
        Returns normalized event data ready for LLM processing.
        """
        normalized = {
            "source_id": raw_event.source_id,
            "timestamp": raw_event.timestamp.isoformat(),
            "raw_content": self._extract_content(raw_event.raw_payload),
            "metadata": raw_event.source_metadata,
        }
        
        # Extract email-specific fields for Gmail events
        if raw_event.source_metadata.get("type") == "gmail":
            payload = raw_event.raw_payload
            subject = payload.get("subject", "")
            from_email = payload.get("from", "").lower()
            
            normalized["subject"] = subject
            normalized["from_email"] = from_email
            
            # Detect "dodaj do kalendarza" in title/subject
            if "dodaj do kalendarza" in subject.lower():
                normalized["metadata"]["prompt_task"] = "extract_mail_to_calendar"
            
            # Detect school/kindergarten based on sender
            elif self._is_school_sender(from_email):
                normalized["metadata"]["prompt_task"] = "extract_school_event"
        
        return normalized
    
    def _is_school_sender(self, from_email: str) -> bool:
        """Check if sender is from school/kindergarten."""
        school_indicators = [
            "szkola", "szkoła", "przedszkole", "edu.pl", 
            "sp", "gimnazjum", "liceum", "nauczyciel", 
            "dyrektor", "sekretariat"
        ]
        return any(indicator in from_email for indicator in school_indicators)
    
    def _extract_content(self, payload: Dict[str, Any]) -> str:
        """Extract text content from payload for LLM processing."""
        if isinstance(payload, dict):
            for field in ["body", "content", "text", "message", "description"]:
                if field in payload:
                    return str(payload[field])
            return str(payload)
        return str(payload)

