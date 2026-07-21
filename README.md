# Lead Outreach System

An internal tool for managing the lead discovery → enrichment → outreach pipeline. Built with FastAPI (backend) and Next.js (frontend), fully containerized with Docker Compose.

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git (to clone the repo)

### 1. Clone and set up environment
```bash
# Clone the project
cd d:\WORK\Website_demo

# The .env file is already included with dev-safe defaults
# Review and modify if needed:
cat .env
```

### 2. Start all services
```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5433
- **Redis** on port 6380
- **FastAPI backend** on port 8000 (with auto-reload)
- **Next.js frontend** on port 3000 (with auto-reload)

The backend will automatically run Alembic migrations on startup.

### 3. Seed the database
```bash
# In a new terminal, seed the database with test data:
docker-compose exec backend python -m app.seed
```

### 4. Open the app
- **Frontend**: http://localhost:3000
- **Backend API docs**: http://localhost:8000/api/docs (Swagger UI)
- **Backend ReDoc**: http://localhost:8000/api/redoc

### Login Credentials (seed data)
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@team.com | admin123 |
| Member | member@team.com | member123 |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://leadoutreach:leadoutreach_secret@postgres:5432/leadoutreach` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens | `dev-secret-key-change-in-production` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `ENCRYPTION_KEY` | Fernet key for API key encryption | Dev key (change in production!) |
| `NEXT_PUBLIC_API_URL` | Backend URL for the frontend | `http://localhost:8000` |

## Project Structure

```
├── docker-compose.yml          # All services defined here
├── .env                        # Environment variables
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini             # Migration configuration
│   ├── alembic/                # Database migrations
│   └── app/
│       ├── main.py             # FastAPI entry point
│       ├── config.py           # Settings from env vars
│       ├── database.py         # Async SQLAlchemy setup
│       ├── deps.py             # Auth dependencies
│       ├── models/             # SQLAlchemy ORM models
│       ├── schemas/            # Pydantic validation schemas
│       ├── routers/            # API endpoint handlers
│       ├── services/           # Business logic (auth, encryption)
│       └── seed.py             # Test data seeder
└── frontend/
    ├── Dockerfile
    ├── src/
    │   ├── app/                # Next.js pages (App Router)
    │   ├── components/         # React components
    │   ├── lib/                # API client, auth, utilities
    │   └── types/              # TypeScript types
    └── public/
```

## API Endpoints

| Group | Endpoints |
|-------|-----------|
| Auth | `POST /api/auth/login`, `POST /api/auth/register`, `POST /api/auth/refresh`, `GET /api/auth/me` |
| Users | `GET /api/users`, `PATCH /api/users/{id}/role`, `PATCH /api/users/{id}/deactivate` |
| Companies | `GET /api/companies`, `GET /api/companies/{id}` |
| Leads | `GET /api/leads`, `GET /api/leads/{id}`, `PATCH /api/leads/{id}/exclude`, `PATCH /api/leads/{id}/status` |
| Enrichment | `GET /api/leads/{id}/enrichment`, `POST /api/leads/{id}/enrichment/trigger` |
| Campaigns | `GET /api/campaigns`, `POST /api/campaigns`, `GET /api/campaigns/{id}`, `POST /api/campaigns/{id}/leads`, `DELETE /api/campaigns/{id}/leads/{lead_id}` |
| Suppression | `GET /api/suppression`, `POST /api/suppression`, `DELETE /api/suppression/{id}` |
| Webhooks | `POST /api/webhooks/email-events` |
| Dashboard | `GET /api/dashboard/stats` |
| Settings | `GET /api/settings`, `PUT /api/settings/{key}` |

## What's NOT Implemented Yet

The following are intentionally left as stubs — they'll be built as separate background worker modules:
- **Scraping** (BrightData) — the actual job posting discovery
- **Enrichment** (Prospeo/Vibe Prospecting) — the actual contact lookup
- **Email Sending** (Instantly) — the actual outreach execution

The database schema, API endpoints, and settings page are all ready for these to be plugged in.

## Common Commands

```bash
# Start all services
docker-compose up --build

# Stop all services
docker-compose down

# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend

# Run seed script
docker-compose exec backend python -m app.seed

# Open a shell in the backend container
docker-compose exec backend bash

# Reset the database (drop volumes and re-seed)
docker-compose down -v
docker-compose up --build
# Then: docker-compose exec backend python -m app.seed
```
