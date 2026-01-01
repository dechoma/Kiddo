"""LLM service integration."""

import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .prompt_manager import PromptManager, Prompt


class LLMService:
    """Service for LLM-based event extraction."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        prompt_manager: Optional[PromptManager] = None,
        prompts_dir: Optional[str] = None
    ):
        """
        Initialize LLM service.
        
        Args:
            api_key: LLM API key
            model: LLM model name
            prompt_manager: Optional PromptManager instance. If None, creates one.
            prompts_dir: Directory containing prompt YAML files (used if prompt_manager is None)
        """
        self.api_key = api_key
        self.model = model
        self.prompt_manager = prompt_manager or PromptManager(prompts_dir=prompts_dir)
        # TODO: Initialize LLM client
    
    async def extract_event_details(
        self,
        normalized_event: Dict[str, Any],
        event_type_hint: Optional[str] = None,
        prompt_task: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send event to LLM and extract structured information using prompts from YAML.
        
        Args:
            normalized_event: Normalized event data
            event_type_hint: Optional hint about event type to select appropriate prompt
            
        Returns:
            Extracted structured event data
        """
        # Get appropriate prompt - prioritize prompt_task, then event_type_hint
        prompt = None
        if prompt_task:
            prompt = self.prompt_manager.get_prompt(prompt_task)
        
        if not prompt and event_type_hint:
            prompt = self.prompt_manager.get_prompt_for_event_type(event_type_hint)
        
        if not prompt:
            # Fallback to default event extraction
            prompt = self.prompt_manager.get_prompt("event_extraction") or \
                     self.prompt_manager.get_prompt("extract_event_details")
        
        if not prompt:
            raise ValueError("No prompt found for event extraction")
        
        # Extract event content
        event_content = normalized_event.get("raw_content", "")
        if not event_content:
            # Try to get content from other fields
            event_content = str(normalized_event.get("raw_payload", ""))
        
        # Prepare template variables based on prompt task
        template_vars = {"event_content": event_content}
        
        # Add email-specific fields for mail_to_calendar prompt
        if prompt_task == "extract_mail_to_calendar":
            template_vars["subject"] = normalized_event.get("subject", "")
            template_vars["from_email"] = normalized_event.get("from_email", "")
        
        # Add email fields for school extraction (if available)
        if prompt_task == "extract_school_event":
            if "subject" in normalized_event:
                template_vars["subject"] = normalized_event.get("subject", "")
            if "from_email" in normalized_event:
                template_vars["from_email"] = normalized_event.get("from_email", "")
        
        # Format prompt with template variables
        system_prompt, user_prompt = self.prompt_manager.format_prompt(
            prompt,
            **template_vars
        )
        
        # TODO: Implement actual LLM API call
        # This should:
        # 1. Call LLM API with system_prompt and user_prompt
        # 2. Parse JSON response
        # 3. Handle errors and retries
        # 4. Validate extracted data
        
        # Placeholder: Simulate LLM response parsing
        # In real implementation, this would call the LLM API
        try:
            # For now, return a placeholder structure
            # Real implementation would parse LLM JSON response
            extracted_data = await self._call_llm_api(system_prompt, user_prompt, prompt)
            return extracted_data
        except Exception as e:
            # Fallback to basic extraction
            print(f"Error calling LLM API: {e}")
            return self._fallback_extraction(normalized_event)
    
    async def _call_llm_api(
        self,
        system_prompt: str,
        user_prompt: str,
        prompt: Prompt
    ) -> Dict[str, Any]:
        """
        Call LLM API with formatted prompts.
        
        TODO: Implement actual LLM API integration (OpenAI, Anthropic, etc.)
        """
        # Placeholder implementation
        # Real implementation would:
        # 1. Initialize LLM client (OpenAI, Anthropic, etc.)
        # 2. Make API call with system and user prompts
        # 3. Parse JSON response
        # 4. Handle rate limiting and retries
        
        # For now, return placeholder structure
        return {
            "event_type": "meeting",
            "title": "Sample Event",
            "description": "",
            "due_date": None,
            "start_time": None,
            "end_time": None,
            "participants": [],
            "location": None,
            "priority": "normal",
        }
    
    def _fallback_extraction(self, normalized_event: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback extraction when LLM API fails."""
        return {
            "event_type": "unknown",
            "title": normalized_event.get("raw_content", "Untitled Event")[:100],
            "description": normalized_event.get("raw_content", ""),
            "due_date": None,
            "start_time": None,
            "end_time": None,
            "participants": [],
            "location": None,
            "priority": "normal",
        }
    
    async def extract_batch(self, normalized_events: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Extract details for multiple events (batch processing)."""
        # TODO: Implement batch extraction for efficiency
        results = []
        for event in normalized_events:
            result = await self.extract_event_details(event)
            results.append(result)
        return results

