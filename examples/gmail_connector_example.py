"""Example usage of Gmail connector."""

import asyncio
from dotenv import load_dotenv
from src.config import load_config
from src.ingestion.adapters import GmailConnector


async def main():
    """Example of using Gmail connector."""
    
    # Load configuration from environment variables
    load_dotenv()  # Load from .env file if present
    system_config = load_config()
    
    # Get Gmail configuration
    if not system_config.gmail:
        print("Error: Gmail configuration not found. Set GMAIL_CREDENTIALS_PATH environment variable.")
        return
    
    # Create connector using config
    connector = GmailConnector("gmail_source_1", system_config.to_gmail_dict())
    
    try:
        # Connect to Gmail
        await connector.connect()
        print("Connected to Gmail")
        
        # Check health
        is_healthy = await connector.health_check()
        print(f"Gmail health check: {is_healthy}")
        
        # Fetch events (emails)
        print("\nFetching emails...")
        count = 0
        async for event in connector.fetch_events():
            count += 1
            print(f"\n--- Event {count} ---")
            print(f"Event ID: {event.event_id}")
            print(f"Timestamp: {event.timestamp}")
            print(f"Subject: {event.raw_payload.get('subject', 'N/A')}")
            print(f"From: {event.raw_payload.get('from', 'N/A')}")
            print(f"Snippet: {event.raw_payload.get('snippet', 'N/A')[:100]}...")
            
            # Limit to first 5 for example
            if count >= 5:
                break
        
        # Update query dynamically
        print("\n\nUpdating query to fetch emails with attachments...")
        connector.set_query("has:attachment is:unread")
        
        # Fetch with new query
        print("Fetching emails with new query...")
        async for event in connector.fetch_events():
            print(f"Found email: {event.raw_payload.get('subject', 'N/A')}")
            break  # Just show first one
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect
        await connector.disconnect()
        print("\nDisconnected from Gmail")


if __name__ == "__main__":
    asyncio.run(main())

