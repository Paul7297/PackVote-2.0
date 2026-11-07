# PackVote

PackVote is a travel-planning platform for group trips. The project brings together trip management, destination voting, weather insights, cost estimation, and AI-guided recommendations so a group can decide on the best destination together.

## Architecture overview

```mermaid
flowchart LR
    User[Web User] --> FE[React + TypeScript frontend\nVite app]
    FE --> API[FastAPI backend\nREST API]
    API --> DB[(PostgreSQL)]
    API --> W[Open-Meteo weather API]
    API --> G[Geoapify place search]
    API --> M[Gemini AI assistant]
```

## Repository layout

- `backend/` — Python FastAPI backend and database models/services
- `frontend/` — React + TypeScript + Vite client
- `docs/` — project documentation and design notes
- `docker/` — container assets (if added by deployment workflow)
- `.github/workflows/` — CI automation

## Local setup

### 1) Configure environment variables

Use the examples in the repo as your starting point.

- Copy `backend/.env.example` to `backend/.env`
- Copy `frontend/.env.example` to `frontend/.env.local`
- For convenience, the root `/.env.example` lists the full local setup used by both layers

Example values:

```env
# backend/.env
DATABASE_URL=postgresql://user:password@localhost:5432/packvote
SECRET_KEY=change-me-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
GEOCODING_PROVIDER=geoapify
GEOAPIFY_API_KEY=your-geoapify-key
GEMINI_API_KEY=your-gemini-key
```

```env
# frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000
```

### 2) Start the database

Use PostgreSQL locally or with Docker Compose:

```bash
docker compose up -d db
```

### 3) Run the backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Run the frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

The frontend is expected to call the backend on `http://localhost:8000` unless you override `VITE_API_BASE_URL`.

## Key backend features

- Authentication and token refresh: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`
- Trip lifecycle: create, list, archive, invite members, manage statuses
- Destination and voting flows: search destinations, confirm candidates, compute vote results
- Recommendation engine: score destinations based on group preferences and trip constraints
- Weather integration: fetch forecast and historical weather data for trip dates
- AI assistant: explain a destination or compare two destinations using Gemini and structured evidence

## Frontend application flow

- Landing and onboarding via auth pages
- Dashboard with trip overview and member management
- Trip detail panel for destination planning and voting
- Recommendation and AI panels for decision support

## Environment variables reference

### Backend

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing secret |
| `ALGORITHM` | Yes | JWT signing algorithm, usually `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | Access token validity length |
| `CORS_ORIGINS` | Yes | Allowed frontend origins |
| `GEOCODING_PROVIDER` | Optional | External geocoding provider (`geoapify` currently default) |
| `GEOAPIFY_API_KEY` | Optional for geocoding | Map/destination lookup provider key |
| `GEMINI_API_KEY` | Optional for AI features | Google Gemini key for AI route generation |

### Frontend

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Yes | Backend origin such as `http://localhost:8000` |

## AI and weather integration

### Weather

The backend weather service in `backend/app/services/weather_service.py` uses Open-Meteo to gather:

- daily forecast data
- historical weather for trip dates
- normalized summaries for destination evaluation

### AI assistant

The AI service in `backend/app/services/ai_assistant_service.py` uses the Gemini REST API to generate destination explanations or comparisons. It always relies on structured evidence (scores, reasons, weather, cost, preferences) and does not invent missing values.

Important contributor note:

- `GEMINI_API_KEY` must be present in `backend/.env` to enable AI responses
- `GEOAPIFY_API_KEY` is required for destination lookup features when geocoding is used
- never commit personal API keys into source control

## Validation and quality gates

Run the project checks locally before opening a PR:

```bash
cd backend
python scripts/validate_api_contracts.py
pytest tests/test_api_contracts.py -q

cd ../frontend
npm run lint
npm run build
```

CI automation is configured in `.github/workflows/ci.yml` to enforce these checks automatically.

## Deployment notes

- Docker Compose is configured for local development with PostgreSQL, the backend, and the frontend
- Container files are present for backend and frontend image builds
- Cloud deployment can use the same service definitions as a starting point for Azure, Docker, or container-hosted environments

## Contributing

1. Create a branch from the main branch
2. Keep backend and frontend config files synced with the examples in this repo
3. Validate route contracts and UI builds before merging
4. Do not commit environment secrets or local-only config files
