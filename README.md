# Vibe App

A FastAPI-based backend application for managing AI agents and their executions.

## Features

- User authentication and authorization
- AI agent management
- Execution tracking
- WebSocket support for real-time updates
- RESTful API endpoints

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic (for database migrations)
- WebSockets
- SQLite (for development)

## Project Structure

```
vibeapp/
├── api/                # API endpoints
│   └── v1/            # API version 1
├── core/              # Core functionality
├── db/                # Database configuration
├── models/            # SQLAlchemy models
├── schemas/           # Pydantic schemas
└── migrations/        # Database migrations
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the development server:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation at `http://localhost:8000/docs`
- ReDoc documentation at `http://localhost:8000/redoc`

## Development

To create new database migrations:
```bash
alembic revision --autogenerate -m "Description of changes"
```

## License

MIT 