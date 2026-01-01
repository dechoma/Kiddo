# Prompts Directory

This directory contains YAML files defining prompts for different LLM extraction tasks.

## Structure

Each prompt file should follow this structure:

```yaml
name: prompt_name
description: Description of what this prompt does
task: task_identifier
system_prompt: |
  System prompt for the LLM
  Can be multi-line
  
user_prompt_template: |
  User prompt template with {placeholders}
  Use {event_content} for the event text
  
output_format: json
```

## Available Prompts

### General Extraction
- **event_extraction.yaml** - General event extraction (default)
- **meeting_extraction.yaml** - Meeting-specific extraction
- **deadline_extraction.yaml** - Deadline/task-specific extraction

### Polish Use Cases
- **school_kindergarten_extraction.yaml** - School/kindergarten event extraction for parents (Polish)
- **mail_to_calendar_extraction.yaml** - Extract events from emails with subject "dodaj do kalendarza" (Polish)
- **sms_summary.yaml** - Generate short SMS summaries (max 160 chars, Polish)

## Adding New Prompts

1. Create a new YAML file in this directory
2. Follow the structure above
3. The prompt will be automatically loaded by `PromptManager`
4. Access it by name or task identifier

## Prompt Selection

The system automatically selects prompts based on:
- Event type hint (if provided)
- Task identifier
- Falls back to `event_extraction` if no match found

## Template Variables

Available variables in `user_prompt_template`:
- `{event_content}` - The main event text/content to extract from

You can add more variables as needed and pass them when formatting the prompt.

