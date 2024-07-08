# IronMonkey Threat Research App

## Overview

This Flask-based web application is designed for threat research and analysis. It provides features for parsing RSS feeds, tagging content using NLP, and searching through parsed content.

## Key Features

- User authentication (login, logout, registration)
- RSS feed parsing and storage
- Content tagging using Diffbot API
- Content summarization using Ollama API
- Advanced search functionality
- Scheduled tasks for processing feeds and generating summaries

## Setup and Configuration

1. Ensure Python 3.x is installed on your system.
2. Install required dependencies (use `pip install -r requirements.txt` if available).
3. Set up environment variables:
   - DIFFBOT_API_KEY
   - OLLAMA_BASE_URL
   - OLLAMA_MODEL (default is "llama3:latest")
   - SECRET_KEY (for Flask app)
4. Initialize the database (SQLite) using Flask-Migrate.

## Running the Application

To run the application, execute the following command:

```
python app.py
```

The app will start in debug mode with auto-reloading disabled.

## Main Components

- **Authentication:** Handled by Flask-Login with custom User model.
- **Database:** SQLAlchemy ORM with models for User, ParsedContent, RSSFeed, and more.
- **RSS Management:** Periodic fetching and parsing of RSS feeds.
- **NLP Tagging:** Content tagging using Diffbot API for entity recognition and categorization.
- **Summarization:** Content summarization using Ollama API.
- **Search:** Advanced search functionality with filtering options.

## API Endpoints

- `GET /`: Home page (requires authentication)
- `GET/POST /login`: User login
- `GET /logout`: User logout
- `GET/POST /register`: User registration
- `POST /tag_content`: Tag content using Diffbot API
- `POST /batch_tag_content`: Batch tag multiple content items
- `GET/POST /search`: Search functionality
- `GET /view/<uuid:item_id>`: View specific content item
- `POST /summarize_content`: Generate summary for content

## Scheduled Tasks

- Check and process empty summaries every 10 minutes
- Check and process RSS feeds every 30 minutes

## Error Handling

The application includes custom error handling and logging for better debugging and user experience.

## Security Considerations

- CSRF protection enabled
- Input sanitization using Bleach library
- Secure handling of API keys and sensitive information

## Future Improvements

- Implement more advanced NLP features
- Enhance the user interface for better data visualization
- Add more customization options for RSS feed management
- Implement user roles and permissions for enhanced access control
