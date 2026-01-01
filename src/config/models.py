"""Configuration data models."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GmailConfig:
    """Gmail connector configuration."""
    credentials_path: str
    token_path: Optional[str] = None  # Path to store OAuth token as JSON file
    query: str = "is:unread"
    max_results: int = 100
    label_ids: Optional[List[str]] = None
    processed_label: str = "kiddo/processed"


@dataclass
class LLMConfig:
    """LLM service configuration."""
    api_key: str
    model: str = "gpt-4"
    provider: str = "openai"
    prompts_dir: Optional[str] = None


@dataclass
class GoogleCalendarConfig:
    """Google Calendar configuration."""
    credentials_path: str


@dataclass
class ICalConfig:
    """iCal provider configuration."""
    url: str


@dataclass
class SMSConfig:
    """SMS channel configuration."""
    api_key: str
    provider: str = "twilio"


@dataclass
class EmailConfig:
    """Email channel configuration."""
    smtp_server: str
    smtp_port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True

