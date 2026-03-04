# Technical Specification

## Architecture

```
app.py
├── ticket_loader.py
├── board_classifier.py
└── topic_scanner.py
```

## Data Flow

1. Load tickets from YAML
2. Query tk CLI for status
3. Classify into columns
4. Display in TUI

## Testing

Use pytest for unit tests, Textual for UI testing.
