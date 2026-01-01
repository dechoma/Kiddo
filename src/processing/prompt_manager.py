"""Prompt management for LLM processing."""

import os
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Prompt:
    """Represents a prompt configuration."""
    name: str
    description: str
    task: str
    system_prompt: str
    user_prompt_template: str
    output_format: str = "json"


class PromptManager:
    """Manages loading and accessing prompts from YAML files."""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt YAML files. 
                        Defaults to 'prompts' directory in project root.
        """
        if prompts_dir is None:
            # Default to prompts directory in project root
            project_root = Path(__file__).parent.parent.parent
            prompts_dir = str(project_root / "prompts")
        
        self.prompts_dir = Path(prompts_dir)
        self.prompts: Dict[str, Prompt] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load all prompt YAML files from the prompts directory."""
        if not self.prompts_dir.exists():
            print(f"Warning: Prompts directory not found: {self.prompts_dir}")
            return
        
        for yaml_file in self.prompts_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    prompt_data = yaml.safe_load(f)
                
                prompt = Prompt(
                    name=prompt_data.get('name', yaml_file.stem),
                    description=prompt_data.get('description', ''),
                    task=prompt_data.get('task', 'extract_event_details'),
                    system_prompt=prompt_data.get('system_prompt', ''),
                    user_prompt_template=prompt_data.get('user_prompt_template', ''),
                    output_format=prompt_data.get('output_format', 'json')
                )
                
                # Index by both name and task
                self.prompts[prompt.name] = prompt
                self.prompts[prompt.task] = prompt
                
            except Exception as e:
                print(f"Error loading prompt from {yaml_file}: {e}")
    
    def get_prompt(self, identifier: str) -> Optional[Prompt]:
        """
        Get a prompt by name or task identifier.
        
        Args:
            identifier: Prompt name or task name
            
        Returns:
            Prompt object or None if not found
        """
        return self.prompts.get(identifier)
    
    def get_prompt_for_event_type(self, event_type: Optional[str] = None) -> Optional[Prompt]:
        """
        Get appropriate prompt based on event type.
        
        Args:
            event_type: Type of event (e.g., "meeting", "deadline", "task")
            
        Returns:
            Prompt object or default prompt if not found
        """
        if event_type:
            # Try to find specific prompt for event type
            type_prompt = self.get_prompt(f"{event_type}_extraction")
            if type_prompt:
                return type_prompt
        
        # Default to general event extraction
        return self.get_prompt("event_extraction") or self.get_prompt("extract_event_details")
    
    def format_prompt(self, prompt: Prompt, **kwargs) -> Tuple[str, str]:
        """
        Format a prompt template with provided values.
        
        Args:
            prompt: Prompt object to format
            **kwargs: Values to substitute in the template
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        user_prompt = prompt.user_prompt_template.format(**kwargs)
        return prompt.system_prompt, user_prompt
    
    def list_prompts(self) -> Dict[str, Prompt]:
        """List all available prompts."""
        return self.prompts.copy()

