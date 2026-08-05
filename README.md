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

### Steps

```bash
# 1. Clone
git clone https://github.com/yourusername/cleardocs.git
cd cleardocs

# 2. Create your .env
cp .env.example .env
# Open .env and set:
#   POSTGRES_PASSWORD=anything-you-like
#   GROQ_API_KEY=your-groq-key-here
#   SECRET_KEY=any-long-random-string

# 3. Start everything
#    Run from the repo root. The compose file lives in infrastructure/ but
#    .env is at the root, so pass both -f and --env-file explicitly.
docker compose -f infrastructure/docker-compose.yml --env-file .env up -d

# 4. Run database migrations
docker compose -f infrastructure/docker-compose.yml --env-file .env exec backend python manage.py migrate

# 5. Create an admin user (optional)
docker compose exec backend python manage.py createsuperuser
```

### Access the services

| Service | URL |
|---|---|
| Frontend | http://localhost |
| API | http://localhost/api/v1/ |
| Django Admin | http://localhost/admin |
| Celery Flower | http://localhost:5555 |
| API Docs | http://localhost/api/v1/schema/swagger/ |

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
