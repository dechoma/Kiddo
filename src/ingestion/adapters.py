"""Source connector implementations."""

import base64
import json
import os
from typing import AsyncIterator
from datetime import datetime
from email.utils import parsedate_to_datetime

from .connector import SourceConnector
from ..models.event import RawEvent


class GmailConnector(SourceConnector):
    """Gmail event source connector with query filtering."""
    
    def __init__(self, source_id: str, config: dict):
        """
        Initialize Gmail connector.
        
        Config should contain:
        - credentials_path: Path to OAuth2 credentials JSON file
        - token_path: Path to store/load OAuth2 token (optional)
        - query: Gmail search query string (e.g., "is:unread", "from:example@email.com")
        - max_results: Maximum messages per fetch (default: 100)
        - label_ids: List of label IDs to search (optional)
        """
        super().__init__(source_id, config)
        self.service = None
        self.query = config.get("query", "")
        self.max_results = config.get("max_results", 100)
        self.label_ids = config.get("label_ids")
        self.processed_label_name = config.get("processed_label", "kiddo/processed")
        self._processed_label_id = None  # Cache the label ID
        self._credentials_path = config.get("credentials_path")
        self._token_path = config.get("token_path")
    
    async def connect(self) -> None:
        """Establish connection to Gmail API."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            # Need modify scope to add/remove labels
            # Note: gmail.modify allows: read, compose, send, and manage labels
            # For deletion, full gmail scope may be needed: https://mail.google.com/
            # But for this connector, label management is sufficient (we don't delete emails)
            SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
            creds = None
            
            # Load existing token from JSON file
            if self._token_path and os.path.exists(self._token_path):
                creds = Credentials.from_authorized_user_file(self._token_path, SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self._credentials_path:
                        raise ValueError("credentials_path is required in config")
                    if not os.path.exists(self._credentials_path):
                        raise FileNotFoundError(
                            f"Credentials file not found: {self._credentials_path}"
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self._credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run as JSON
                if self._token_path:
                    with open(self._token_path, 'w') as token:
                        token.write(creds.to_json())
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            
            # Ensure processed label exists
            await self._ensure_processed_label()
            
        except ImportError:
            raise ImportError(
                "Gmail connector requires google-api-python-client, "
                "google-auth-httplib2, google-auth-oauthlib. "
                "Install with: pip install google-api-python-client "
                "google-auth-httplib2 google-auth-oauthlib"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Gmail: {e}")
    
    async def disconnect(self) -> None:
        """Close connection to Gmail API."""
        if self.service:
            self.service.close()
            self.service = None
    
    async def fetch_events(self) -> AsyncIterator[RawEvent]:
        """
        Fetch emails from Gmail matching the query.
        
        Yields RawEvent for each email message.
        Supports incremental fetching (only new messages).
        """
        if not self.service:
            raise RuntimeError("Not connected to Gmail. Call connect() first.")
        
        try:
            # Build query parameters
            query_params = {
                'q': self.query,
                'maxResults': self.max_results,
            }
            
            if self.label_ids:
                query_params['labelIds'] = self.label_ids
            
            # List messages
            results = self.service.users().messages().list(
                userId='me',
                **query_params
            ).execute()
            
            messages = results.get('messages', [])
            
            for message_item in messages:
                message_id = message_item['id']
                
                # Get full message
                message = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
                
                # Convert to RawEvent
                raw_event = self._message_to_event(message)
                
                # Check if already processed (has kiddo/processed label)
                if await self.is_processed(raw_event):
                    continue
                
                yield raw_event
                
        except Exception as e:
            raise RuntimeError(f"Error fetching Gmail events: {e}")
    
    def _message_to_event(self, message: dict) -> RawEvent:
        """Convert Gmail message to RawEvent."""
        # Extract headers
        headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
        
        # Extract timestamp
        date_header = headers.get('Date')
        if date_header:
            try:
                timestamp = parsedate_to_datetime(date_header)
            except (ValueError, TypeError):
                timestamp = datetime.fromtimestamp(int(message['internalDate']) / 1000)
        else:
            timestamp = datetime.fromtimestamp(int(message['internalDate']) / 1000)
        
        # Extract body content
        body_text = self._extract_message_body(message.get('payload', {}))
        
        # Build payload
        payload = {
            'id': message['id'],
            'threadId': message.get('threadId'),
            'snippet': message.get('snippet', ''),
            'body': body_text,
            'headers': headers,
            'subject': headers.get('Subject', ''),
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'cc': headers.get('Cc', ''),
            'date': timestamp.isoformat(),
            'labels': message.get('labelIds', []),
        }
        
        # Build metadata
        metadata = {
            'type': 'gmail',
            'message_id': message['id'],
            'thread_id': message.get('threadId'),
            'history_id': message.get('historyId'),
            'size_estimate': message.get('sizeEstimate'),
        }
        
        return RawEvent(
            source_id=self.source_id,
            timestamp=timestamp,
            raw_payload=payload,
            source_metadata=metadata,
            event_id=f"gmail_{message['id']}"
        )
    
    def _extract_message_body(self, payload: dict) -> str:
        """Extract text body from message payload."""
        body_text = ""
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                # Recursively handle nested parts
                if 'parts' in part:
                    body_text += self._extract_message_body(part)
                else:
                    # Extract text/plain or text/html
                    mime_type = part.get('mimeType', '')
                    if mime_type in ['text/plain', 'text/html']:
                        data = part.get('body', {}).get('data')
                        if data:
                            try:
                                decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                                body_text += decoded + "\n"
                            except Exception:
                                pass
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            if mime_type in ['text/plain', 'text/html']:
                data = payload.get('body', {}).get('data')
                if data:
                    try:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8')
                    except Exception:
                        pass
        
        return body_text.strip()
    
    async def health_check(self) -> bool:
        """Check if Gmail API is accessible."""
        if not self.service:
            return False
        
        try:
            # Try to get profile to verify connection
            profile = self.service.users().getProfile(userId='me').execute()
            return profile is not None
        except Exception:
            return False
    
    async def _ensure_processed_label(self) -> None:
        """Ensure the processed label exists in Gmail, create if it doesn't."""
        if not self.service:
            return
        
        try:
            # Get or create the label
            label_id = await self._get_or_create_label(self.processed_label_name)
            self._processed_label_id = label_id
        except Exception as e:
            # If label creation fails, log but don't fail the connection
            print(f"Warning: Could not ensure processed label exists: {e}")
    
    async def _get_or_create_label(self, label_name: str) -> str:
        """Get existing label ID or create new label."""
        if not self.service:
            raise RuntimeError("Not connected to Gmail")
        
        # List all labels
        labels = self.service.users().labels().list(userId='me').execute()
        
        # Check if label already exists
        for label in labels.get('labels', []):
            if label.get('name') == label_name:
                return label['id']
        
        # Create new label if it doesn't exist
        label_body = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        
        created_label = self.service.users().labels().create(
            userId='me',
            body=label_body
        ).execute()
        
        return created_label['id']
    
    async def is_processed(self, event: RawEvent) -> bool:
        """
        Check if Gmail message has been processed by checking for processed label.
        
        Note: This method is not in the base interface but is used internally
        by fetch_events to skip already processed messages.
        """
        if not event.event_id or not self.service:
            return False
        
        # Extract message ID from event_id (format: "gmail_{message_id}")
        message_id = event.event_id.replace("gmail_", "")
        
        try:
            # Get message to check its labels
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='metadata',
                metadataHeaders=['']
            ).execute()
            
            # Get processed label ID if not cached
            if not self._processed_label_id:
                await self._ensure_processed_label()
            
            # Check if message has the processed label
            label_ids = message.get('labelIds', [])
            return self._processed_label_id in label_ids if self._processed_label_id else False
            
        except Exception as e:
            # If we can't check, assume not processed
            print(f"Error checking if message is processed: {e}")
            return False
    
    async def mark_as_processed(self, event: RawEvent) -> bool:
        """Mark Gmail message as processed by applying label."""
        if not event.event_id or not self.service:
            return False
        
        # Extract message ID from event_id (format: "gmail_{message_id}")
        message_id = event.event_id.replace("gmail_", "")
        
        try:
            # Ensure processed label exists
            if not self._processed_label_id:
                await self._ensure_processed_label()
            
            if not self._processed_label_id:
                print("Warning: Could not get processed label ID")
                return False
            
            # Apply the label to the message
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [self._processed_label_id]}
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error marking message as processed: {e}")
            return False
    
    def set_query(self, query: str) -> None:
        """
        Update the Gmail search query.
        
        Args:
            query: Gmail search query string
                  Examples:
                  - "is:unread"
                  - "from:example@email.com"
                  - "subject:meeting"
                  - "has:attachment"
                  - "after:2024/1/1 before:2024/12/31"
        """
        self.query = query

