# Event Processing and Calendar Integration System

A generic system for processing events from multiple sources, extracting structured information using LLM, and integrating with calendar systems and notification channels.

## Architecture

This system implements the architecture described in `HLD.md`:

- **Event Ingestion Layer**: Connectors for various event sources (API, webhooks, files, databases)
- **Event Queue**: Buffering and decoupling layer
- **Processing Engine**: Normalization, LLM extraction, and validation
- **Calendar Integration**: Support for Google Calendar and iCal
- **Notification Engine**: Multi-channel notification delivery (SMS, email)

## Project Structure

```
kiddo/
├── src/
│   ├── models/          # Data models
│   ├── ingestion/       # Source connectors
│   ├── queue/           # Event queue
│   ├── processing/      # Processing engine
│   ├── calendar/        # Calendar integration
│   ├── notifications/   # Notification engine
│   └── orchestrator.py  # Main orchestration
├── creds/               # Credentials directory (excluded from git)
├── main.py              # Entry point
├── connectors.yaml      # Connector configurations
└── README.md           # This file
```

## Usage

### Setup

1. **Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install dependencies**:
```bash
# Install base + dev dependencies (uv manages .venv automatically)
uv sync

# Or install with specific optional dependencies:
uv sync --extra gmail         # Gmail connector dependencies
uv sync --extra llm           # LLM dependencies
uv sync --extra calendar      # Calendar dependencies
uv sync --extra notifications # Notification dependencies
uv sync --extra all           # All optional dependencies

# Install multiple extras:
uv sync --extra gmail --extra llm
```

3. **Run commands**:
```bash
# Run scripts (uv automatically uses the managed environment)
uv run python main.py

# Run tests
uv run pytest

# Run any command in the managed environment
uv run <command>
```

4. **Configure the system**:
   - Create `creds/` directory and place all credential files there (e.g., `creds/gmail_credentials.json`)
   - Copy `.env.example` to `.env` (or create your own `.env` file)
   - Set environment variables for your configuration
   - Create `connectors.yaml` based on `connectors.yaml.example`
   - See Configuration section below for details
   
   **Note**: The `creds/` directory is excluded from git for security. Store all OAuth credentials, tokens, and API keys there.

5. **Run the system**:
```bash
uv run python main.py
```

6. **Run tests**:
```bash
uv run pytest
uv run pytest tests/integration -m integration
```

## Configuration

The system uses a centralized configuration management system:

- **Environment Variables**: Load from `.env` file or system environment
- **Type-safe Config Classes**: Defined in `src/config/` module
- **YAML Configuration**: Connector configurations in `connectors.yaml`
- **Single Source of Truth**: All configuration loaded via `load_config()`

### Configuration Options

All configuration is done via environment variables. See `.env.example` for a complete list.

Key configuration sections:
- **Gmail**: `GMAIL_*` variables
- **LLM**: `LLM_*` variables  
- **Calendar**: `GOOGLE_CALENDAR_*`, `ICAL_*` variables
- **Notifications**: `SMS_*`, `EMAIL_*` variables


## Gmail Connector

The Gmail connector allows fetching emails from Gmail using Gmail search queries.

### Setup

1. **Create Google Cloud Project and enable Gmail API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - **Important**: The connector uses `gmail.modify` scope which allows reading, modifying labels, and sending messages
   - **Note**: `gmail.modify` does not allow permanent deletion of messages (requires full `https://mail.google.com/` scope)
   - Download credentials JSON file to `creds/` directory (e.g., `creds/gmail_credentials.json`)

2. **Install dependencies**:
```bash
uv sync --extra gmail
```

### Usage

```python
from src.ingestion import GmailConnector

config = {
    "credentials_path": "creds/gmail_credentials.json",
    "token_path": "creds/gmail_token.json",  # Optional
    "query": "is:unread subject:meeting",  # Gmail search query
    "max_results": 100,
    "processed_label": "kiddo/processed",  # Optional: label name for processed emails (default: "kiddo/processed")
}

connector = GmailConnector("gmail_source", config)
await connector.connect()

# Fetch emails matching query
async for event in connector.fetch_events():
    print(f"Subject: {event.raw_payload.get('subject')}")
    print(f"Body: {event.raw_payload.get('body')}")

# Update query dynamically
connector.set_query("has:attachment from:important@example.com")
```

### Processed Event Tracking

The Gmail connector automatically tracks processed events using Gmail labels:
- When an event is successfully processed, the connector applies the `kiddo/processed` label (or custom label name)
- On subsequent fetches, emails with this label are automatically skipped
- The label is created automatically if it doesn't exist
- You can customize the label name via the `processed_label` config option

**Note**: The connector requires `gmail.modify` scope (not just `gmail.readonly`) to apply labels. This scope allows label management but does not allow permanent deletion of messages.

### Query Examples

- `"is:unread"` - Unread emails
- `"subject:meeting"` - Emails with "meeting" in subject
- `"from:example@email.com"` - Emails from specific sender
- `"has:attachment"` - Emails with attachments
- `"after:2024/1/1 before:2024/12/31"` - Date range
- `"label:INBOX label:IMPORTANT"` - Multiple labels
- Combine queries: `"is:unread subject:meeting has:attachment"`
- Exclude processed: `"-label:kiddo/processed"` - Exclude already processed emails

See [Gmail search operators](https://support.google.com/mail/answer/7190) for full query syntax.

## Prompt Management

The system uses YAML files to manage LLM prompts for different extraction tasks.

### Prompt Structure

Prompts are stored in the `prompts/` directory as YAML files. Each prompt file defines:
- System prompt (instructions for the LLM)
- User prompt template (with placeholders like `{event_content}`)
- Task identifier
- Output format

### Available Prompts

- **event_extraction.yaml** - General event extraction (default)
- **meeting_extraction.yaml** - Meeting-specific extraction
- **deadline_extraction.yaml** - Deadline/task-specific extraction

### Adding Custom Prompts

1. Create a new YAML file in `prompts/` directory
2. Follow the structure defined in existing prompts
3. The system automatically loads and makes it available
4. Access by name or task identifier

### Configuration

Set `LLM_PROMPTS_DIR` environment variable to use a custom prompts directory (defaults to `prompts/` in project root).

See `prompts/README.md` for detailed documentation.

## Use Cases

### 1. School/Kindergarten Event Extraction
Extract time-sensitive events from school/kindergarten messages for parent calendar.

**Prompt**: `school_kindergarten_extraction.yaml`
- Automatically detected for messages containing school-related keywords
- Extracts: events, trips, meetings, payment deadlines, performances
- Includes: what child should bring, required parent response
- Customizable alerts (default: 60 minutes before)

**Example**: Parent receives email from school about field trip → System extracts date, time, location, what to bring → Adds to parent calendar with alert

### 2. SMS Summary Generation
Generate short SMS summaries (max 160 characters) of events.

**Prompt**: `sms_summary.yaml`
- Creates concise summaries for SMS notifications
- Includes: what, when, where
- Respects 160 character limit
- Polish language support

**Usage**:
```python
from src.processing import SMSGenerator

sms_gen = SMSGenerator(llm_service)
sms_text = await sms_gen.generate_sms(event, max_length=160)
```

### 3. Mail to Calendar Service
Extract events from emails with subject "dodaj do kalendarza" (add to calendar).

**Prompt**: `mail_to_calendar_extraction.yaml`
- Automatically triggered when email subject contains "dodaj do kalendarza"
- Extracts time-sensitive events from email body
- Supports recurring events
- Customizable alerts per event

**Flow**:
1. Email arrives with subject "dodaj do kalendarza"
2. System extracts event details (date, time, location, participants)
3. Event is added to calendar with customizable alert
4. Calendar sends reminder at specified time before event

### Calendar Alerts

All calendar events support customizable alerting:
- **alert_before_minutes**: Minutes before event for reminder (default: 15)
- Alerts are automatically configured when creating calendar events
- Multiple alerts can be set (e.g., 1 day before + 15 minutes before)
- Works with Google Calendar and other providers

**Example**:
- School event: 60 minutes before (time to prepare child)
- Meeting: 15 minutes before (standard reminder)
- Deadline: 1 day before (important deadline reminder)

## Next Steps

1. Implement remaining connector types (API, Webhook, File, Database)
2. Integrate actual LLM API (OpenAI, Anthropic, etc.)
3. Implement calendar provider APIs (Google Calendar, iCal)
4. Implement notification channel delivery (Twilio, SendGrid)
5. Add proper message queue (Redis, RabbitMQ, Kafka)
6. Add error handling and retry logic
7. Add monitoring and logging
8. Add more comprehensive tests

