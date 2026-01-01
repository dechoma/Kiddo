"""Main entry point for the system."""

import asyncio
from dotenv import load_dotenv
from src.config import load_config
from src.orchestrator import SystemOrchestrator
from src.ingestion import GmailConnector
from src.queue import InMemoryEventQueue
from src.processing import (
    EventProcessingEngine,
    EventNormalizer,
    LLMService,
    DataExtractor
)
from src.calendar import GoogleCalendarProvider, ICalProvider
from src.notifications import NotificationEngine, SMSChannel, EmailChannel


async def main():
    """Initialize and start the system."""
    
    # Load configuration from environment variables
    load_dotenv()  # Load from .env file if present
    config = load_config()
    
    # Initialize connectors from connectors.yaml
    connectors = []
    
    for connector_def in config.get_connectors():
        connector_type = connector_def.get('type')
        connector_name = connector_def.get('name', f"{connector_type}_connector")
        source_id = connector_def.get('source_id', connector_name)
        
        if connector_type == 'gmail':
            # Convert connector definition to Gmail config dict
            gmail_config = {
                "credentials_path": connector_def.get('credentials_path'),
                "token_path": connector_def.get('token_path'),
                "query": connector_def.get('query', 'is:unread'),
                "max_results": connector_def.get('max_results', 100),
                "processed_label": connector_def.get('processed_label', 'kiddo/processed'),
                "label_ids": connector_def.get('label_ids'),
            }
            connectors.append(GmailConnector(source_id, gmail_config))
        
        elif connector_type == 'api':
            # TODO: Initialize API connector
            # connectors.append(APIConnector(source_id, connector_def))
            pass
        
        elif connector_type == 'webhook':
            # TODO: Initialize Webhook connector
            # connectors.append(WebhookConnector(source_id, connector_def))
            pass
        
        elif connector_type == 'file':
            # TODO: Initialize File connector
            # connectors.append(FileConnector(source_id, connector_def))
            pass
        
        elif connector_type == 'database':
            # TODO: Initialize Database connector
            # connectors.append(DatabaseConnector(source_id, connector_def))
            pass
    
    # Add other connectors (can be configured via env or hardcoded for now)
    # connectors.append(APIConnector("api_source_1", {"endpoint": "https://api.example.com"}))
    # connectors.append(WebhookConnector("webhook_source_1", {"port": 8080}))
    
    event_queue = InMemoryEventQueue()
    
    # Initialize processing engine
    normalizer = EventNormalizer()
    if config.llm:
        llm_config = config.to_llm_dict()
        # PromptManager will be created inside LLMService if not provided
        llm_service = LLMService(**llm_config)
    else:
        llm_service = LLMService(api_key="")  # Will fail if not configured
    extractor = DataExtractor()
    processing_engine = EventProcessingEngine(
        normalizer=normalizer,
        llm_service=llm_service,
        extractor=extractor
    )
    
    # Initialize calendar providers
    calendar_providers = {}
    if config.google_calendar:
        calendar_providers["google"] = GoogleCalendarProvider(config.to_google_calendar_dict())
    if config.ical:
        calendar_providers["ical"] = ICalProvider(config.to_ical_dict())
    
    # Initialize notification channels
    notification_channels = {}
    if config.sms:
        notification_channels["sms"] = SMSChannel(config.to_sms_dict())
    if config.email:
        notification_channels["email"] = EmailChannel(config.to_email_dict())
    notification_engine = NotificationEngine(channels=notification_channels)
    
    # Create orchestrator
    orchestrator = SystemOrchestrator(
        connectors=connectors,
        event_queue=event_queue,
        processing_engine=processing_engine,
        calendar_providers=calendar_providers,
        notification_engine=notification_engine
    )
    
    # Start system
    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        print("Shutting down...")
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())

