"""SMS summary generation for events."""

from typing import Dict, Any, Optional

from ..models.event import StructuredEvent
from .llm_service import LLMService
from .prompt_manager import PromptManager


class SMSGenerator:
    """Generate short SMS summaries of events."""
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize SMS generator.
        
        Args:
            llm_service: LLM service instance (shares prompt manager)
        """
        self.llm_service = llm_service
        self.prompt_manager = llm_service.prompt_manager
    
    async def generate_sms(self, event: StructuredEvent, max_length: int = 160) -> str:
        """
        Generate SMS summary for an event.
        
        Args:
            event: Structured event to summarize
            max_length: Maximum SMS length (default 160)
            
        Returns:
            SMS text (max max_length characters)
        """
        # Get SMS summary prompt
        prompt = self.prompt_manager.get_prompt("sms_summary") or \
                 self.prompt_manager.get_prompt("generate_sms_summary")
        
        if not prompt:
            # Fallback to simple summary
            return self._fallback_sms(event, max_length)
        
        # Format prompt with event data
        system_prompt, user_prompt = self.prompt_manager.format_prompt(
            prompt,
            title=event.title or "Wydarzenie",
            description=event.description or "",
            start_time=event.start_time.isoformat() if event.start_time else "",
            end_time=event.end_time.isoformat() if event.end_time else "",
            location=event.location or "",
            event_type=event.event_type or "event",
            additional_info=self._format_additional_info(event)
        )
        
        # TODO: Call LLM to generate SMS
        # For now, return fallback
        sms_text = await self._call_llm_for_sms(system_prompt, user_prompt, max_length)
        
        # Ensure it's within max_length
        if len(sms_text) > max_length:
            sms_text = sms_text[:max_length-3] + "..."
        
        return sms_text
    
    async def _call_llm_for_sms(
        self,
        system_prompt: str,
        user_prompt: str,
        max_length: int
    ) -> str:
        """Call LLM to generate SMS summary."""
        # TODO: Implement actual LLM call
        # For now, return placeholder
        return "Wydarzenie: [placeholder - implement LLM call]"
    
    def _format_additional_info(self, event: StructuredEvent) -> str:
        """Format additional event information for SMS prompt."""
        info_parts = []
        
        if event.participants:
            info_parts.append(f"Uczestnicy: {', '.join(event.participants[:3])}")
        
        if event.priority and event.priority != "normal":
            info_parts.append(f"Priorytet: {event.priority}")
        
        if event.alert_before_minutes:
            info_parts.append(f"Przypomnienie: {event.alert_before_minutes} min przed")
        
        return "\n".join(info_parts) if info_parts else ""
    
    def _fallback_sms(self, event: StructuredEvent, max_length: int) -> str:
        """Generate simple SMS without LLM."""
        parts = []
        
        # Title
        if event.title:
            parts.append(event.title[:50])
        
        # Time
        if event.start_time:
            time_str = event.start_time.strftime("%d.%m %H:%M")
            parts.append(time_str)
        
        # Location (if short)
        if event.location and len(event.location) < 30:
            parts.append(event.location)
        
        sms = " | ".join(parts)
        
        if len(sms) > max_length:
            sms = sms[:max_length-3] + "..."
        
        return sms


