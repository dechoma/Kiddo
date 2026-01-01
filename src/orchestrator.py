"""Main system orchestrator."""

import asyncio
from typing import Dict, List

from .ingestion import SourceConnector
from .queue import EventQueue
from .processing import EventProcessingEngine
from .calendar import CalendarProvider
from .notifications import NotificationEngine
from .models.event import RawEvent, StructuredEvent
from .models.calendar import CalendarEvent


class SystemOrchestrator:
    """Main orchestrator for event processing system."""
    
    def __init__(
        self,
        connectors: List[SourceConnector],
        event_queue: EventQueue,
        processing_engine: EventProcessingEngine,
        calendar_providers: Dict[str, CalendarProvider],
        notification_engine: NotificationEngine
    ):
        """Initialize orchestrator with all components."""
        self.connectors = connectors
        # Map source_id to connector for marking events as processed
        self.connector_map = {connector.source_id: connector for connector in connectors}
        self.event_queue = event_queue
        self.processing_engine = processing_engine
        self.calendar_providers = calendar_providers
        self.notification_engine = notification_engine
        self.running = False
    
    async def start(self):
        """Start the system."""
        self.running = True
        
        # Connect all source connectors
        for connector in self.connectors:
            await connector.connect()
        
        # Start ingestion tasks
        ingestion_tasks = [
            self._ingestion_loop(connector)
            for connector in self.connectors
        ]
        
        # Start processing task
        processing_task = self._processing_loop()
        
        # Run all tasks
        await asyncio.gather(*ingestion_tasks, processing_task)
    
    async def stop(self):
        """Stop the system."""
        self.running = False
        
        # Disconnect all connectors
        for connector in self.connectors:
            await connector.disconnect()
    
    async def _ingestion_loop(self, connector: SourceConnector):
        """Ingestion loop for a connector."""
        while self.running:
            try:
                async for event in connector.fetch_events():
                    await self.event_queue.publish(event)
            except Exception as e:
                # TODO: Handle errors, retry logic
                print(f"Error in ingestion loop for {connector.source_id}: {e}")
                await asyncio.sleep(5)  # Backoff
    
    async def _processing_loop(self):
        """Main processing loop."""
        while self.running:
            try:
                async for raw_event in self.event_queue.consume():
                    try:
                        # Process event
                        structured_event = await self.processing_engine.process_event(
                            raw_event
                        )
                        
                        # Integrate with calendar
                        await self._integrate_calendar(structured_event)
                        
                        # Send notifications if needed
                        await self._send_notifications(structured_event)
                        
                        # Mark event as processed in source connector
                        connector = self.connector_map.get(raw_event.source_id)
                        if connector:
                            await connector.mark_as_processed(raw_event)
                        
                        # Acknowledge event
                        await self.event_queue.ack(raw_event.event_id or "")
                        
                    except Exception as e:
                        # TODO: Handle processing errors
                        print(f"Error processing event: {e}")
                        await self.event_queue.nack(
                            raw_event.event_id or "",
                            requeue=True
                        )
            except Exception as e:
                print(f"Error in processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _integrate_calendar(self, event: StructuredEvent):
        """Integrate event with calendar providers."""
        # TODO: Determine which calendar(s) to use based on configuration
        for provider_name, provider in self.calendar_providers.items():
            try:
                # Get default calendar ID (should come from config)
                calendar_id = "primary"  # TODO: Get from config
                
                calendar_event = await provider.create_event(
                    event,
                    calendar_id
                )
                
                # TODO: Store calendar_event mapping
                
            except Exception as e:
                # TODO: Handle calendar errors
                print(f"Error integrating with {provider_name}: {e}")
    
    async def _send_notifications(self, event: StructuredEvent):
        """Send notifications for event."""
        # TODO: Determine notification rules based on event type, priority, etc.
        # For now, skip notifications (can be configured)
        pass

