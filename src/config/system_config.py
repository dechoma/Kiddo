"""Main system configuration."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import GmailConfig
from .connectors_loader import load_connectors_from_file
from .env_loader import (
    load_llm_config,
    load_google_calendar_config,
    load_ical_config,
    load_sms_config,
    load_email_config
)


@dataclass
class SystemConfig:
    """Main system configuration."""
    connectors: List[Dict] = field(default_factory=list)
    llm: Optional[object] = None
    google_calendar: Optional[object] = None
    ical: Optional[object] = None
    sms: Optional[object] = None
    email: Optional[object] = None
    
    @property
    def gmail_connectors(self) -> Dict[int, GmailConfig]:
        """Get Gmail connectors as dict for backward compatibility."""
        gmail_dict = {}
        for idx, conn in enumerate(self.connectors, start=1):
            if conn.get('type') == 'gmail':
                gmail_dict[idx] = GmailConfig(
                    credentials_path=conn.get('credentials_path', ''),
                    token_path=conn.get('token_path'),
                    query=conn.get('query', 'is:unread'),
                    max_results=int(conn.get('max_results', 100)),
                    processed_label=conn.get('processed_label', f"kiddo/processed_{idx}"),
                    label_ids=conn.get('label_ids'),
                )
        return gmail_dict
    
    @property
    def gmail(self) -> Optional[GmailConfig]:
        """Backward compatibility: return first Gmail config if exists."""
        gmail_conns = self.gmail_connectors
        if gmail_conns:
            return list(gmail_conns.values())[0]
        return None
    
    @classmethod
    def from_env(cls) -> "SystemConfig":
        """Load configuration from environment variables and files."""
        config = cls()
        
        # Load connectors from YAML file
        config.connectors = load_connectors_from_file()
        
        # Load other configurations from environment
        config.llm = load_llm_config()
        config.google_calendar = load_google_calendar_config()
        config.ical = load_ical_config()
        config.sms = load_sms_config()
        config.email = load_email_config()
        
        return config
    
    def to_gmail_dict(self, instance_num: int = 1) -> Dict:
        """Convert Gmail config to dictionary for connector."""
        gmail_config = self.gmail_connectors.get(instance_num)
        if not gmail_config:
            return {}
        return {
            "credentials_path": gmail_config.credentials_path,
            "token_path": gmail_config.token_path,
            "query": gmail_config.query,
            "max_results": gmail_config.max_results,
            "label_ids": gmail_config.label_ids,
            "processed_label": gmail_config.processed_label,
        }
    
    def get_connectors(self) -> List[Dict]:
        """Get all connector configurations."""
        return self.connectors.copy()
    
    def get_gmail_configs(self) -> Dict[int, GmailConfig]:
        """Get all Gmail connector configurations (backward compatibility)."""
        return self.gmail_connectors
    
    # Helper methods for converting configs to dicts
    def to_llm_dict(self) -> Dict:
        """Convert LLM config to dictionary for service."""
        if not self.llm:
            return {}
        result = {"api_key": self.llm.api_key, "model": self.llm.model}
        if self.llm.prompts_dir:
            result["prompts_dir"] = self.llm.prompts_dir
        return result
    
    def to_google_calendar_dict(self) -> Dict:
        """Convert Google Calendar config to dictionary."""
        if not self.google_calendar:
            return {}
        return {"credentials": self.google_calendar.credentials_path}
    
    def to_ical_dict(self) -> Dict:
        """Convert iCal config to dictionary."""
        if not self.ical:
            return {}
        return {"url": self.ical.url}
    
    def to_sms_dict(self) -> Dict:
        """Convert SMS config to dictionary."""
        if not self.sms:
            return {}
        return {"api_key": self.sms.api_key}
    
    def to_email_dict(self) -> Dict:
        """Convert Email config to dictionary."""
        if not self.email:
            return {}
        return {
            "smtp_server": self.email.smtp_server,
            "smtp_port": self.email.smtp_port,
            "username": self.email.username,
            "password": self.email.password,
            "use_tls": self.email.use_tls,
        }


# Global config instance
_config: Optional[SystemConfig] = None


def load_config() -> SystemConfig:
    """Load and return system configuration."""
    global _config
    if _config is None:
        _config = SystemConfig.from_env()
    return _config


def get_config() -> SystemConfig:
    """Get current system configuration."""
    if _config is None:
        return load_config()
    return _config

