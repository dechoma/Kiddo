# Tests

## Running Tests

### All Tests
```bash
uv run pytest
```

### Integration Tests Only
```bash
uv run pytest tests/integration -m integration
```

### With Coverage
```bash
uv run pytest --cov=src --cov-report=html
```

## Gmail Connector Integration Tests

The Gmail connector integration tests require a real Gmail account and credentials.

### Setup

1. **Create Gmail API Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - **Important**: The connector uses `gmail.modify` scope which allows:
     - Reading emails
     - Modifying labels
     - Sending messages (if needed)
   - **Note**: `gmail.modify` does not allow permanent deletion of messages. Test cleanup removes labels from test emails instead of deleting them.
   - Download credentials JSON file to `creds/` directory (e.g., `creds/gmail_credentials.json`)

2. **Set Environment Variables**:
   ```bash
   export TEST_GMAIL_CREDENTIALS_PATH="creds/gmail_credentials.json"
   export TEST_GMAIL_TOKEN_PATH="creds/test_gmail_token.json"  # Optional
   export TEST_GMAIL_QUERY="your-gmail-query"  # Optional, default: "is:unread -label:kiddo/test_processed newer_than:3d"
   export TEST_GMAIL_PROCESSED_LABEL="your-processed-label"  # Optional, default: "kiddo/test_processed"
   ```

   Or create a `.env.test` file:
   ```bash
   TEST_GMAIL_CREDENTIALS_PATH=creds/gmail_credentials.json
   TEST_GMAIL_TOKEN_PATH=creds/test_gmail_token.json
   TEST_GMAIL_QUERY=your-gmail-query
   TEST_GMAIL_PROCESSED_LABEL=your-processed-label
   ```
   
   **Note**: If `TEST_GMAIL_QUERY` is not set, it defaults to `"is:unread -label:{TEST_GMAIL_PROCESSED_LABEL} newer_than:3d"` to fetch only unread emails without the processed label, received in the last 3 days.

3. **Run Tests**:
   ```bash
   uv run pytest tests/integration/test_gmail_connector.py -v
   ```

### Test Coverage

The integration tests cover:
- ✅ Connecting to Gmail API
- ✅ Health check
- ✅ Fetching events/emails
- ✅ Marking events as processed
- ✅ Checking if events are processed
- ✅ Query filtering
- ✅ Event structure validation
- ✅ Updating query dynamically

### Notes

- Tests use a test-specific label (`kiddo/test`) to identify and clean up test emails
- Tests create test emails automatically and clean them up after running
- Test cleanup removes labels from test emails (does not delete them, as `gmail.modify` scope doesn't allow deletion)
- Tests limit the number of fetched events to avoid long test runs
- Tests skip if credentials are not configured (useful for CI/CD)
- Tests use module-scoped fixtures to share connectors and test emails across all tests for efficiency

