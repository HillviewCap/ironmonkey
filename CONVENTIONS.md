**conventions.md**
**Project Structure**
your_flask_project/
├── app/
│   ├── __init__.py  # Application factory
│   ├── models/
│   │   ├── __init__.py
│   │   ├── relational/  # SQLAlchemy models
│   │   │   └── __init__.py
│   │   └── graph/  # PyGremlin models
│   │       └── __init__.py
│   ├── blueprints/
│   │   ├── main/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── routes.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── http_client.py  # httpx client
│   │   └── ollama_client.py  # Ollama integration
│   ├── services/
│   │   ├── __init__.py
│   │   └── data_processing.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   └── integration/
├── migrations/  # For database migrations
├── .env  # Environment variables
├── .gitignore
├── requirements.txt
├── README.md
├── CONVENTIONS.md
└── run.py  # Entry point for running the application

**General**

* Follow PEP 8 guidelines for Python code formatting and style.
* Use meaningful and descriptive variable and function names.
* Keep functions short and focused on a single task.
* Use docstrings to document functions and modules.

**Libraries and Dependencies**

* Prefer `httpx` over `requests` for making HTTP requests.
* Use `SQLAlchemy` as the ORM for interacting with the relational database.
* Use `PyGremlin` for interacting with the graph database.
* Use `Ollama` for local language model integration.
* Use `langchain-community` for all AI/ML/NER/NLP functions.

**Type Hints and Annotations**

* Use type hints and annotations everywhere possible to ensure code readability and maintainability.
* Use `from __future__ import annotations` to enable postponed evaluation of type hints.

**Database and Data Storage**

* Use a consistent naming convention for database tables and columns (e.g., `snake_case`).
* Use `uuid` as the primary key for all database tables.
* Store raw content from diverse sources in the relational database with proper source citation.
* Use the graph database for storing relationships between entities.

**Security**

* Implement authentication and authorization using `Flask-Login` and `Flask-Principal`.
* Enable HTTPS encryption using a trusted SSL/TLS certificate.
* Implement input validation and sanitation to prevent SQL injection and cross-site scripting (XSS) attacks.
* Ensure secure storage of sensitive data, such as API keys and database credentials.

**Frontend**

* Use a modern and clean CSS framework `Tailwind CSS` for UI components.
* Use `JavaScript` and `HTML` templates to build the frontend, with a focus on responsiveness and accessibility.
* Use a consistent naming convention for CSS classes and HTML IDs (e.g., `kebab-case`).

**Testing**

* Write comprehensive unit tests and integration tests for all functionality.
* Use `pytest` as the testing framework.
* Use `mocking` to isolate dependencies and ensure testing efficiency.

**Code Organization**

* Organize code into logical modules and packages, with a focus on separation of concerns.
* Use a consistent naming convention for modules and packages (e.g., `snake_case`).
* Keep the `models` package separate from the `routes` package.

**Flask Application Structure**

* Organize your Flask application using the application factory pattern.
* Keep the main application logic in a separate module (e.g., `app.py`).
* Use blueprints to organize routes and views for better modularity.

**API Development**

* Follow RESTful principles when designing APIs.
* Use versioning in your API endpoints (e.g., `/api/v1/resource`).
* Return appropriate HTTP status codes for different responses.

**Frontend Integration**

* Use AJAX or Fetch API for asynchronous communication between the frontend and Flask backend.
* Ensure that the frontend can handle CORS (Cross-Origin Resource Sharing) if hosted on a different domain.

* Use `environment variables` to store sensitive information, such as API keys and database credentials.
* Follow the principle of least privilege when setting up access controls for the platform.
