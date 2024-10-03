# IronMonkey Threat Research App

## Overview

This Flask-based web application is designed for threat research and analysis. It provides features for parsing RSS feeds, tagging content using NLP, searching through parsed content, and managing APT groups.

## How to Install
1. Clone the repository to your machine
2. Copy the .env.example and rename to .env
3. Fill out the .env with your api keys
4. Create a virtual environment: conda create -n ironmonkey python=3.11 -y
5. activate ironmonkey
6. cd into the ironmonkey directory
7. install the requirements: pip install -r requirements.txt -U
8. start the service: python run.py
9. navigate to the home page: http://127.0.0.1:5000/
10. Create an account and log in

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
   - SUMMARY_API_CHOICE (options: "ollama" or "groq")
   - OLLAMA_BASE_URL (if using Ollama)
   - GROQ_API_KEY (if using Groq)
   - FLASK_ENV (development or production)
   - FLASK_PORT (default is 5000)
4. Initialize the database: `flask db upgrade`

## Running the Application

To run the application, execute:

```
python run.py
```

The app will start based on the FLASK_ENV setting (development or production).

## Main Components

- **Authentication:** Handled by Flask-Login
- **Database:** SQLAlchemy ORM for relational data, PyGremlin for graph data
- **RSS Management:** Periodic fetching and parsing of RSS feeds
- **Summarization:** Content summarization using Ollama or Groq API
- **Search:** Advanced search functionality with filtering options
- **APT Groups:** Management and analysis of APT (Advanced Persistent Threat) groups

## Scheduled Tasks

- Process RSS feeds (configurable interval)
- Generate summaries for new content (configurable interval)

## Error Handling and Logging

The application includes custom error handling and comprehensive logging for better debugging and user experience.

## Future Improvements

- Implement more advanced NLP features
- Add more customization options for RSS feed management
- Implement user roles and permissions for enhanced access control
- Integrate with additional threat intelligence sources

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
