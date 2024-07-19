# IronMonkey Threat Research App

## Overview

This Flask-based web application is designed for threat research and analysis. It provides features for parsing RSS feeds, tagging content using NLP, searching through parsed content, and managing APT groups.

## Key Features

- User authentication (login, logout, registration)
- RSS feed parsing and storage
- Content tagging using Diffbot API
- Content summarization using Ollama or Groq API
- Advanced search functionality
- APT group management
- RESTful API for data access
- Scheduled tasks for processing feeds and generating summaries

## Setup and Configuration

1. Ensure Python 3.x is installed on your system.
2. Install required dependencies: `pip install -r requirements.txt`
3. Set up environment variables in a `.env` file:
   - DIFFBOT_API_KEY
   - SUMMARY_API_CHOICE (options: "ollama" or "groq")
   - OLLAMA_BASE_URL (if using Ollama)
   - GROQ_API_KEY (if using Groq)
   - SECRET_KEY (for Flask app)
   - FLASK_ENV (development or production)
   - FLASK_PORT (default is 5000)
4. Initialize the database: `flask db upgrade`

## Running the Application

To run the application, execute:

```
python run.py
```

The app will start based on the FLASK_ENV setting (development or production).

## Project Structure

- `app/`: Main application package
  - `blueprints/`: Feature-specific routes and views
  - `models/`: Database models (relational and graph)
  - `services/`: Business logic
  - `utils/`: Helper functions and classes
  - `static/`: Static files (CSS, JS, images)
  - `templates/`: HTML templates
- `tests/`: Unit and integration tests
- `migrations/`: Database migration scripts

## Main Components

- **Authentication:** Handled by Flask-Login
- **Database:** SQLAlchemy ORM for relational data, PyGremlin for graph data
- **RSS Management:** Periodic fetching and parsing of RSS feeds
- **NLP Tagging:** Content tagging using Diffbot API
- **Summarization:** Content summarization using Ollama or Groq API
- **Search:** Advanced search functionality with filtering options
- **APT Groups:** Management and analysis of APT (Advanced Persistent Threat) groups

## API Endpoints

- `/api/v1/content`: CRUD operations for parsed content
- `/api/v1/rss_feeds`: Manage RSS feeds
- `/api/v1/apt_groups`: APT group information
- `/api/v1/search`: Advanced search endpoint

For full API documentation, refer to the Swagger/OpenAPI documentation (available at `/api/docs` when running the app).

## Scheduled Tasks

- Process RSS feeds (configurable interval)
- Generate summaries for new content (configurable interval)

## Error Handling and Logging

The application includes custom error handling and comprehensive logging for better debugging and user experience.

## Security Considerations

- CSRF protection using Flask-WTF
- Input sanitization using Bleach library
- Secure handling of API keys and sensitive information
- HTTPS enforcement in production using Flask-Talisman

## Testing

Run tests using pytest:

```
pytest
```

## Future Improvements

- Implement more advanced NLP features
- Enhance the user interface using modern frontend frameworks
- Add more customization options for RSS feed management
- Implement user roles and permissions for enhanced access control
- Integrate with additional threat intelligence sources

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
