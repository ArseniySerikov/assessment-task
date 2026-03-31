# Travel Planner API

A RESTful API for managing travel projects and places to visit, powered by the [Art Institute of Chicago API](https://api.artic.edu/docs/).

## Overview

This project was built as a Python backend assessment focused on:
- designing RESTful CRUD endpoints,
- working with a relational database,
- integrating a third-party API,
- and implementing practical business rules.

## Tech Stack

- Python + FastAPI
- SQLAlchemy ORM + SQLite
- httpx (async third-party API calls)
- cachetools (TTL cache for external API responses)
- Docker + Docker Compose

## Implemented Features

- Full CRUD for travel projects
- Create project with places in one request
- Add places to existing projects
- Add/update notes for places
- Mark places as visited
- Auto-complete project when all places are visited
- Validate place existence using Art Institute API
- Pagination and filtering for project listing
- In-memory caching of third-party API responses
- OpenAPI/Swagger documentation

## Business Rules

- A project must contain from **1 to 10 places** at creation time.
- The same external place cannot be added to the same project more than once.
- A project cannot be deleted if any of its places are marked as visited.
- A project is automatically marked as completed when all its places are visited.

## Quick Start

### Run with Docker (recommended)

```bash
docker compose up --build
```

API base URL: `http://localhost:8000`

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API base URL: `http://localhost:8000`

## API Documentation

OpenAPI documentation is available and used instead of a Postman collection:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Configuration

You can configure the app via environment variables (or `.env` file):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./travel_planner.db` | SQLAlchemy database URL |
| `ARTIC_API_BASE_URL` | `https://api.artic.edu/api/v1` | Art Institute API base URL |
| `ARTIC_CACHE_TTL` | `300` | Cache TTL in seconds |
| `ARTIC_CACHE_MAX_SIZE` | `512` | Max cached external responses |
| `MAX_PLACES_PER_PROJECT` | `10` | Max places allowed per project |

## Endpoints

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/check` | Health check |

### Projects

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/projects/` | Create project with places (1..10) |
| GET | `/api/v1/projects/` | List projects (pagination + filters) |
| GET | `/api/v1/projects/{id}` | Get single project with places |
| PATCH | `/api/v1/projects/{id}` | Update project fields |
| DELETE | `/api/v1/projects/{id}` | Delete project (blocked if visited place exists) |

Project list query params:
- `page` (default: 1)
- `page_size` (default: 20, max: 100)
- `is_completed` (optional bool)
- `search` (optional project name search)

### Places

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/projects/{id}/places/` | Add place to project |
| GET | `/api/v1/projects/{id}/places/` | List places in project |
| GET | `/api/v1/projects/{id}/places/{place_id}` | Get one place |
| PATCH | `/api/v1/projects/{id}/places/{place_id}` | Update notes / visited status |

Places list query params:
- `is_visited` (optional bool)

## Example Requests

### Create a project with places

```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chicago Art Tour",
    "description": "Must-see artworks",
    "start_date": "2026-05-01",
    "places": [
      {"external_id": 27992},
      {"external_id": 129884}
    ]
  }'
```

### Add place to existing project

```bash
curl -X POST http://localhost:8000/api/v1/projects/1/places/ \
  -H "Content-Type: application/json" \
  -d '{"external_id": 20684}'
```

### Update place notes

```bash
curl -X PATCH http://localhost:8000/api/v1/projects/1/places/1 \
  -H "Content-Type: application/json" \
  -d '{"notes": "Need to visit in the morning."}'
```

### Mark place as visited

```bash
curl -X PATCH http://localhost:8000/api/v1/projects/1/places/1 \
  -H "Content-Type: application/json" \
  -d '{"is_visited": true}'
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Settings via pydantic-settings
│   ├── database.py          # SQLAlchemy engine and session
│   ├── models.py            # ORM models (Project, ProjectPlace)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── projects.py      # Project CRUD endpoints
│   │   └── places.py        # Place endpoints
│   └── services/
│       ├── __init__.py
│       └── artic_api.py     # Art Institute API client with caching
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```
