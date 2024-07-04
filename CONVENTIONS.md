**conventions.md**

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

**Misc**

* Use `environment variables` to store sensitive information, such as API keys and database credentials.
* Follow the principle of least privilege when setting up access controls for the platform.
