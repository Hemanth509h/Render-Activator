# Render Pinger

## Overview

Render Pinger is a simple Flask web application designed to keep Render.com free-tier services alive by periodically pinging their URLs. Free-tier Render services spin down after periods of inactivity, and this tool prevents that by sending regular HTTP requests to configured endpoints.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Application Structure

- **Framework**: Flask (Python web framework)
- **Architecture Pattern**: Single-file monolithic application (`main.py`)
- **Data Storage**: In-memory list for URL storage (no persistence across restarts)
- **Background Processing**: Python threading for periodic URL pinging

### Key Components

1. **Web Interface**: Bootstrap-styled HTML form for adding/removing URLs
2. **URL Management**: Simple list-based storage with add/remove operations
3. **Pinger Service**: Background thread that periodically sends HTTP requests to stored URLs

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| In-memory storage | Keeps the app simple; acceptable for a utility tool where persistence isn't critical |
| Single-file structure | Minimal complexity for a focused, single-purpose application |
| Bootstrap CDN | Quick styling without build tooling overhead |
| Threading for background pinger | Allows continuous pinging while serving web requests |

### Routes

- `/` - Main page displaying URL list and add form
- `/add` - POST endpoint to add new URLs
- `/remove` - POST endpoint to remove URLs

## External Dependencies

### Python Packages

- **Flask**: Web framework for serving the UI and handling requests
- **requests**: HTTP library for pinging external URLs

### Frontend Resources

- **Bootstrap 5.3.0**: CSS framework loaded via CDN for responsive styling

### Notes

- No database integration currently exists
- No authentication mechanism implemented
- URLs are lost on application restart (consider adding database persistence if needed)