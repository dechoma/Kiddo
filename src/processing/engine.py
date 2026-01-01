"""Event processing engine."""

from typing import Optional

from ..models.event import RawEvent, StructuredEvent
from .normalizer import EventNormalizer
from .llm_service import LLMService
from .extractor import DataExtractor


class EventProcessingEngine:
    """Main event processing engine."""
    
    def __init__(
        self,
        normalizer: EventNormalizer,
        llm_service: LLMService,
        extractor: DataExtractor
    ):
        """Initialize processing engine."""
        self.normalizer = normalizer
        self.llm_service = llm_service
        self.extractor = extractor
    
    async def process_event(self, raw_event: RawEvent) -> StructuredEvent:
        """
        Process raw event through normalization, LLM extraction, and validation.
        
        Flow:
        1. Normalize raw event to canonical format
        2. Send to LLM for extraction
        3. Extract and validate structured data
        4. Return structured event
        """
        # Step 1: Normalize
        normalized = await self.normalizer.normalize(raw_event)
        
        # Step 2: Determine event type hint and prompt task
        event_type_hint = None
        prompt_task = normalized.get("metadata", {}).get("prompt_task")
        
        # Step 3: LLM extraction with appropriate prompt
        extraction_result = await self.llm_service.extract_event_details(
            normalized,
            event_type_hint=event_type_hint,
            prompt_task=prompt_task
        )
        
        # Step 3: Extract and validate
        structured = await self.extractor.extract(
            normalized,
            extraction_result
        )
        
        return structured
    
    async def process_batch(self, raw_events: list[RawEvent]) -> list[StructuredEvent]:
        """Process multiple events in batch."""
        # TODO: Implement batch processing with parallelization
        results = []
        for event in raw_events:
            try:
                structured = await self.process_event(event)
                results.append(structured)
            except Exception as e:
                # TODO: Handle errors, send to dead-letter queue
                print(f"Error processing event {event.event_id}: {e}")
        return results

