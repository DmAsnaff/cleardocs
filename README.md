# ClearDocs

AI document simplifier and multi-language translator for legal, medical, and government documents.

Upload any complex document → get a plain-language explanation, key clauses highlighted, risk flags, a Q&A chatbot, and translation into 50+ languages. Free. Privacy-first.

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5 + Django REST Framework |
| Frontend | Next.js 14 (App Router) + Tailwind CSS + shadcn/ui |
| Database | PostgreSQL 16 + pgvector |
| Task Queue | Celery 5 + Redis 7 |
| Real-time | Django Channels (WebSockets) |
| LLM | OpenAI / Groq (free) / Anthropic — provider-abstracted |
| OCR | pdfplumber + pytesseract |
| Auth | JWT (simplejwt) |
| CI/CD | GitHub Actions → AWS ECS Fargate |

## Local Setup (5 minutes)

### Prerequisites
- Docker Desktop (with Docker Compose)
- A free [Groq API key](https://console.groq.com) (no credit card required)

### First-time setup

```bash
# 1. Clone
git clone https://github.com/DmAsnaff/cleardocs.git
cd cleardocs

# 2. Create your .env (from the repo root)
cp .env.example .env
# Open .env and set:
#   POSTGRES_PASSWORD=anything-you-like
#   GROQ_API_KEY=your-groq-key-here   (free at https://console.groq.com)
#   SECRET_KEY=any-long-random-string
```

## Running the app

Run every command from the repo root (`ClearDoc/`). The compose file lives in
`infrastructure/` but `.env` is at the root, so pass both `-f` and `--env-file`.

For convenience, set an alias once per terminal:

```bash
alias dc='docker compose -f infrastructure/docker-compose.yml --env-file .env'
```

**1. Start Docker Desktop** and wait until it reports "running".

**2. Start the backend stack** (Postgres, Redis, Django API, Celery worker):

```bash
dc up -d postgres redis backend celery_worker
# (without the alias:)
# docker compose -f infrastructure/docker-compose.yml --env-file .env up -d postgres redis backend celery_worker
```

**3. Start the frontend** (in a second terminal):

```bash
npm --prefix frontend run dev
```

**4. Open the app:**

| Service | URL |
|---|---|
| Frontend (the app) | http://localhost:3000 |
| API | http://localhost:8000/api/v1/ |
| Django Admin | http://localhost:8000/admin |

Log in with `e2e@test.local` / `TestPass123!`, or register a new account.

### Notes

- **Migrations** are already applied and persist in the Postgres volume — no need
  to re-run them. If you ever wipe the volume, run:
  `dc exec backend python manage.py migrate`
- **Create an admin user** (optional): `dc exec backend python manage.py createsuperuser`
- **Stop everything:** `dc down`, then `Ctrl+C` in the frontend terminal.
- The `nginx` and `frontend` Docker services exist for a full containerised run,
  but are resource-heavy. Running the frontend with `npm` (step 3) is the
  recommended path for local development.
- When running the frontend outside Docker, `frontend/.env.local` points it at the
  backend directly (`http://localhost:8000`). This file is created for local dev
  and is gitignored.

## Development Workflow

```bash
# Run backend tests
cd backend
pytest

# Run frontend type check + lint
cd frontend
npx tsc --noEmit
npm run lint

# Stop all services
cd infrastructure
docker compose down

# View backend logs
docker compose logs -f backend

# View Celery worker logs
docker compose logs -f celery_worker
```

## Project Structure

```
cleardocs/
├── backend/          # Django API, Celery tasks, LLM services
├── frontend/         # Next.js 14 app
├── nginx/            # Reverse proxy config
├── infrastructure/   # docker-compose files, AWS task definitions
├── .github/          # CI/CD workflows
├── docs/             # Architecture docs, ADRs
├── .env.example      # Copy this to .env
├── IMPLEMENTATION_PLAN.md
└── TODO.md
```

## LLM Provider

By default this project uses **Groq** (free tier, no credit card needed). To switch providers, set `LLM_PROVIDER` in your `.env`:

```bash
LLM_PROVIDER=groq      # Free — recommended for development
LLM_PROVIDER=openai    # Paid — ~$0.05/document on gpt-4o-mini
LLM_PROVIDER=anthropic # Paid — best quality on long documents
```

## Sprint Progress

See [TODO.md](TODO.md) for the full build tracker.

Current state: **Sprints 1–6 code-complete; app boots and backend test suite passes (78 passed).** Sprint 7 code present (not yet runtime-verified); Sprint 8 (AWS) not provisioned.
