"""Load configuration from environment variables."""

import os
from typing import Optional

from .models import (
    LLMConfig,
    GoogleCalendarConfig,
    ICalConfig,
    SMSConfig,
    EmailConfig
)


def load_llm_config() -> Optional[LLMConfig]:
    """Load LLM configuration from environment."""
    if not os.getenv("LLM_API_KEY"):
        return None
    
    return LLMConfig(
        api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("LLM_MODEL", "gpt-4"),
        provider=os.getenv("LLM_PROVIDER", "openai"),
        prompts_dir=os.getenv("LLM_PROMPTS_DIR"),
    )


def load_google_calendar_config() -> Optional[GoogleCalendarConfig]:
    """Load Google Calendar configuration from environment."""
    if not os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH"):
        return None
    
    return GoogleCalendarConfig(
        credentials_path=os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH"),
    )


def load_ical_config() -> Optional[ICalConfig]:
    """Load iCal configuration from environment."""
    if not os.getenv("ICAL_URL"):
        return None
    
    return ICalConfig(url=os.getenv("ICAL_URL"))


def load_sms_config() -> Optional[SMSConfig]:
    """Load SMS configuration from environment."""
    if not os.getenv("SMS_API_KEY"):
        return None
    
    return SMSConfig(
        api_key=os.getenv("SMS_API_KEY"),
        provider=os.getenv("SMS_PROVIDER", "twilio"),
    )


def load_email_config() -> Optional[EmailConfig]:
    """Load Email configuration from environment."""
    if not os.getenv("EMAIL_SMTP_SERVER"):
        return None
    
    return EmailConfig(
        smtp_server=os.getenv("EMAIL_SMTP_SERVER"),
        smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
        username=os.getenv("EMAIL_USERNAME"),
        password=os.getenv("EMAIL_PASSWORD"),
        use_tls=os.getenv("EMAIL_USE_TLS", "true").lower() == "true",
    )

