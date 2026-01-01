"""Integration tests for Gmail connector using real Gmail account."""

import os
import sys
import base64
import asyncio
import pytest
import pytest_asyncio
from email.mime.text import MIMEText

from src.ingestion.adapters import GmailConnector
from src.models.event import RawEvent


# Test configuration
TEST_LABEL_NAME = "kiddo/test"
GMAIL_INDEXING_DELAY = 2  # seconds to wait for Gmail indexing


@pytest.fixture(scope="module")
def gmail_config():
    """Get Gmail configuration from environment variables."""
    credentials_path = os.getenv("TEST_GMAIL_CREDENTIALS_PATH")
    token_path = os.getenv("TEST_GMAIL_TOKEN_PATH", "test_gmail_token.json")
    
    if not credentials_path:
        pytest.skip("TEST_GMAIL_CREDENTIALS_PATH not set")
    
    processed_label = os.getenv("TEST_GMAIL_PROCESSED_LABEL", "kiddo/test_processed")
    default_query = os.getenv("TEST_GMAIL_QUERY")
    if default_query is None:
        default_query = f"is:unread -label:{processed_label} newer_than:3d"
    
    return {
        "credentials_path": credentials_path,
        "token_path": token_path,
        "query": default_query,
        "max_results": 10,
        "processed_label": processed_label,
    }


@pytest_asyncio.fixture(scope="module")
async def gmail_connector(gmail_config):
    """Create and connect Gmail connector for testing."""
    connector = GmailConnector("test_gmail_source", gmail_config)
    try:
        await connector.connect()
        yield connector
    finally:
        await connector.disconnect()


# Helper functions
async def _get_or_create_test_label(service, label_name):
    """Get or create a test label."""
    try:
        labels = service.users().labels().list(userId='me').execute()
        for label in labels.get('labels', []):
            if label.get('name') == label_name:
                return label['id']
        
        label_body = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        created = service.users().labels().create(userId='me', body=label_body).execute()
        return created['id']
    except Exception:
        return None


async def _cleanup_test_emails(service, test_label_name, test_label_id):
    """Clean up test emails by removing label (deletion requires full scope)."""
    if not service or not test_label_id:
        return
    
    try:
        # Find all messages with test label
        results = service.users().messages().list(
            userId='me', labelIds=[test_label_id], maxResults=100
        ).execute()
        message_ids = [msg['id'] for msg in results.get('messages', [])]
        
        # Handle pagination
        while 'nextPageToken' in results:
            results = service.users().messages().list(
                userId='me', labelIds=[test_label_id], maxResults=100,
                pageToken=results['nextPageToken']
            ).execute()
            message_ids.extend([msg['id'] for msg in results.get('messages', [])])
        
        # Remove label from all test emails
        for message_id in message_ids:
            try:
                service.users().messages().modify(
                    userId='me', id=message_id,
                    body={'removeLabelIds': [test_label_id]}
                ).execute()
            except Exception:
                pass  # Best effort
    except Exception:
        pass  # Best effort


async def _create_test_email(service, subject, body):
    """Create a test email via Gmail API."""
    try:
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress')
        
        message = MIMEText(body)
        message['to'] = user_email
        message['subject'] = subject
        message['from'] = user_email
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId='me', body={'raw': raw_message}
        ).execute()
        return result.get('id')
    except Exception:
        return None


async def _fetch_first_event(connector):
    """Fetch the first event from connector."""
    async for event in connector.fetch_events():
        return event
    return None


@pytest_asyncio.fixture(scope="module")
async def test_emails(gmail_connector):
    """Create test emails with test label once for all tests."""
    test_emails_data = [
        ('Test Event - Meeting Tomorrow', 'Reminder: Meeting tomorrow at 10:00 AM'),
        ('School Event - Field Trip', 'Dear Parents, Field trip to Museum on Friday'),
        ('dodaj do kalendarza - Dentist Appointment', 'Dentist appointment on Wednesday'),
    ]
    
    test_label_id = None
    if gmail_connector.service:
        test_label_id = await _get_or_create_test_label(gmail_connector.service, TEST_LABEL_NAME)
        await _cleanup_test_emails(gmail_connector.service, TEST_LABEL_NAME, test_label_id)
        
        # Create and label test emails
        for subject, body in test_emails_data:
            message_id = await _create_test_email(gmail_connector.service, subject, body)
            if message_id and test_label_id:
                try:
                    gmail_connector.service.users().messages().modify(
                        userId='me', id=message_id,
                        body={'addLabelIds': [test_label_id]}
                    ).execute()
                except Exception:
                    pass
    
    yield
    
    # Cleanup
    if gmail_connector.service:
        await _cleanup_test_emails(gmail_connector.service, TEST_LABEL_NAME, test_label_id)


# Tests
@pytest.mark.integration
@pytest.mark.asyncio
async def test_connect(gmail_config):
    """Test connecting to Gmail API."""
    connector = GmailConnector("test_gmail_source", gmail_config)
    try:
        await connector.connect()
        assert connector.service is not None
    finally:
        await connector.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check(gmail_connector):
    """Test health check."""
    assert await gmail_connector.health_check() is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_events(gmail_connector, test_emails):
    """Test fetching events from Gmail."""
    await asyncio.sleep(GMAIL_INDEXING_DELAY)
    
    events = []
    async for event in gmail_connector.fetch_events():
        events.append(event)
        if len(events) >= 5:
            break
    
    assert len(events) > 0
    for event in events:
        assert isinstance(event, RawEvent)
        assert event.source_id == "test_gmail_source"
        assert event.timestamp is not None
        assert event.raw_payload is not None
        assert "subject" in event.raw_payload
        assert event.event_id is not None
        assert event.event_id.startswith("gmail_")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mark_as_processed(gmail_connector, test_emails):
    """Test marking an event as processed."""
    await asyncio.sleep(GMAIL_INDEXING_DELAY)
    
    event = await _fetch_first_event(gmail_connector)
    assert event is not None
    
    is_processed_before = await gmail_connector.is_processed(event)
    assert await gmail_connector.mark_as_processed(event) is True
    assert await gmail_connector.is_processed(event) is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_is_processed(gmail_connector, test_emails):
    """Test checking if event is processed."""
    await asyncio.sleep(GMAIL_INDEXING_DELAY)
    
    event = await _fetch_first_event(gmail_connector)
    assert event is not None
    assert isinstance(await gmail_connector.is_processed(event), bool)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_set_query(gmail_connector):
    """Test updating the query."""
    original = gmail_connector.query
    gmail_connector.set_query("is:unread subject:test")
    assert gmail_connector.query == "is:unread subject:test"
    gmail_connector.set_query(original)  # Reset


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_structure(gmail_connector, test_emails):
    """Test that events have the expected structure."""
    await asyncio.sleep(GMAIL_INDEXING_DELAY)
    
    event = await _fetch_first_event(gmail_connector)
    assert event is not None
    
    # Verify structure
    assert hasattr(event, 'source_id')
    assert hasattr(event, 'timestamp')
    assert hasattr(event, 'raw_payload')
    assert hasattr(event, 'source_metadata')
    assert hasattr(event, 'event_id')
    
    payload = event.raw_payload
    assert isinstance(payload, dict)
    assert "id" in payload
    assert "subject" in payload
    assert "from" in payload
    
    assert event.source_metadata["type"] == "gmail"
    assert "message_id" in event.source_metadata