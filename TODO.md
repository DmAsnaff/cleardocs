# ClearDocs — Build Tracker

Track progress sprint by sprint. Mark tasks as done by changing `[ ]` to `[x]`.

**Legend:** `[ ]` Not started · `[~]` In progress · `[x]` Done · `[-]` Skipped

> **Build status (2026-08-05):** Repo initialized as a monorepo; first runnable
> state reached. Initial Django migrations generated for all apps (with a
> `VectorExtension` op for pgvector), migrations apply cleanly, and the full
> backend test suite passes (**78 passed**). Sprints 1–6 are code-complete;
> Sprint 7 code exists but is not yet runtime-verified; Sprint 8 (AWS) not
> provisioned. Known issues: `groq`/`httpx` version incompatibility breaks live
> LLM calls (tests use the mock provider); `docker compose` must be run from the
> repo root with `--env-file .env` because `.env` lives at the root.

---

## Phase 1 — Foundation (Weeks 1–2)

### Sprint 1: Project Scaffolding & Infrastructure

**Backend setup**
- [x] Create monorepo structure (`backend/`, `frontend/`, `nginx/`, `infrastructure/`, `docs/`)
- [x] `django-admin startproject config .` inside `backend/`
- [x] Install backend dependencies: DRF, simplejwt, django-storages, django-channels, celery, redis, psycopg2, django-anymail, pdfplumber, pytesseract, python-docx, boto3, sentry-sdk, python-json-logger, factory_boy, pytest-django, ruff, black, mypy
- [x] Split settings: `base.py`, `development.py`, `staging.py`, `production.py`, `test.py`
- [x] Configure `asgi.py` for Django Channels
- [x] Configure `celery.py` app init
- [x] Create `requirements/base.txt`, `requirements/development.txt`, `requirements/production.txt`

**Frontend setup**
- [x] `create-next-app@14 --typescript --tailwind --app` inside `frontend/`
- [x] Install shadcn/ui: `npx shadcn@latest init`
- [x] Install frontend dependencies: axios, zustand, @tanstack/react-query, react-hook-form, zod, react-dropzone, react-pdf, next-intl, lucide-react

**Docker & infrastructure**
- [x] Write `docker-compose.yml` with: postgres (pgvector), redis, clamav, backend, celery_worker, celery_beat, flower, frontend, nginx
- [x] Write `backend/Dockerfile` (multi-stage: development + production)
- [x] Write `frontend/Dockerfile` (multi-stage: development + production)
- [x] Write `nginx/Dockerfile` + `nginx/nginx.conf` (reverse proxy + rate limiting)
- [x] Create `.env.example` with all required variables documented
- [~] Verify `docker compose up` starts all services successfully (postgres, redis, backend build + migrations verified; frontend/nginx/celery not yet smoke-tested)

**CI/CD**
- [x] Write `.github/workflows/backend.yml` (pytest + ruff + black + mypy)
- [x] Write `.github/workflows/frontend.yml` (eslint + tsc + build)
- [x] Write `.github/workflows/deploy.yml` (ECR + ECS deployment)
- [x] Write `.pre-commit-config.yaml` (ruff, black, eslint, prettier)
- [x] Write `README.md` with full local setup instructions

**Deliverable:** `docker compose up` → all services green. CI passes on first push.

---

### Sprint 2: Authentication System

**Backend**
- [x] Create `CustomUser` model extending `AbstractBaseUser` in `apps/users/models.py`
- [x] Run and apply initial migration (`docker compose exec backend python manage.py makemigrations && migrate`) — generated for all apps; pgvector `VectorExtension` added to documents/0001
- [x] `POST /api/v1/auth/register/` — email + password, uniqueness check
- [x] Email verification: generate signed token, send via django-anymail (console in dev)
- [x] `POST /api/v1/auth/login/` — returns access token in body + refresh token in HttpOnly cookie
- [x] `POST /api/v1/auth/token/refresh/` — reads cookie, rotates token
- [x] `POST /api/v1/auth/logout/` — blacklists refresh token, clears cookie
- [x] `POST /api/v1/auth/verify-email/` — verify with signed token
- [x] `POST /api/v1/auth/password-reset/` — send reset email (no email enumeration)
- [x] `POST /api/v1/auth/password-reset/confirm/` — confirm reset with signed token
- [x] `GET/PATCH /api/v1/auth/me/` — profile read + update
- [x] `DELETE /api/v1/auth/me/` — GDPR soft-delete (deleted_at + is_active=False)
- [x] Rate limiting on login: 5/min via DRF ScopedRateThrottle
- [x] Write tests: register, login, refresh, logout, email verification, profile, soft-delete

**Frontend**
- [x] Register page with React Hook Form + Zod validation
- [x] Login page — access token in memory, refresh token in HttpOnly cookie
- [x] Axios interceptors: attach access token, auto-refresh on 401, retry original request
- [x] Zustand auth store: `{ user, isAuthenticated, isLoading, login, logout, fetchProfile }`
- [x] `ProtectedRoute` component — restores session via cookie on mount
- [x] Email verification landing page (`/verify-email?token=...`)

---

## Phase 2 — Core Features (Weeks 3–6)

### Sprint 3: Document Upload & Pipeline Foundation

**Backend**
- [x] `Document` model + migrations (status, s3_key, mime_type, expires_at, etc.)
- [x] `DocumentChunk` model + migrations
- [x] `POST /api/v1/documents/` — multipart upload endpoint
  - [x] Server-side MIME type validation (python-magic)
  - [x] File extension allowlist (.pdf, .docx, .jpg, .jpeg, .png)
  - [x] 50MB file size limit (Nginx + Django)
  - [x] ClamAV virus scan before S3 upload
  - [x] Upload file to S3/local with UUID key
  - [x] Create `Document` DB record with status = `pending`
  - [x] Enqueue Celery pipeline task
- [x] `GET /api/v1/documents/` — list user's documents (cursor-based pagination)
- [x] `GET /api/v1/documents/{id}/` — get document + status
- [x] `DELETE /api/v1/documents/{id}/` — delete document + S3 + analysis
- [x] `GET /api/v1/documents/{id}/status/` — lightweight status poll
- [x] `extract_text` Celery task: pdfplumber → pytesseract fallback → python-docx
- [x] `chunk_document` Celery task: semantic splitting (section → paragraph → sentence)
- [x] Django Channels setup: `ASGI_APPLICATION`, Redis channel layer config, routing
- [x] `DocumentProgressConsumer`: JWT-authenticated WebSocket consumer → forwards progress events
- [x] `JwtAuthMiddleware`: ASGI middleware authenticates WS connections via `?token=` query param
- [x] S3 signed URL generation (15-minute expiry)
- [x] Write tests: upload, validation rejection, list, detail, delete, status endpoints

**Frontend**
- [x] `DropZone.tsx` component: react-dropzone, file type + size validation, drag feedback
- [x] `LanguageSelector.tsx`: ISO 639-1 list, 15 languages
- [x] `CategorySelector.tsx`: Legal / Medical / Government / Financial / Other
- [x] `useDocumentProgress.ts` hook: WebSocket connection + reconnect logic + progress state
- [x] `ProgressTracker.tsx`: animated stage breadcrumbs + progress bar
- [x] `/upload` page assembled with all components

---

### Sprint 4: AI Analysis Engine

**Backend**
- [x] `LLMProvider` abstract base class in `services/llm/base.py`
- [x] `GroqProvider` (free dev), `OpenAIProvider`, `AnthropicProvider`, `MockProvider` implementations
- [x] `services/llm/factory.py` — reads `LLM_PROVIDER` env var, returns singleton
- [x] Versioned prompt templates in `services/llm/prompts.py`:
  - [x] Simplification prompt (v1)
  - [x] Clause extraction prompt (v1)
  - [x] Risk extraction prompt (v1)
  - [x] Date/deadline extraction prompt (v1)
- [x] `DocumentAnalysis` model (summary, simplified_text, clauses/risks/key_dates JSONFields, cost tracking)
- [x] Parallel Celery chord tasks in `tasks/analysis.py`:
  - [x] `generate_summary` task
  - [x] `extract_clauses` task
  - [x] `extract_risks` task
  - [x] `extract_dates` task
  - [x] `generate_embeddings` task (pgvector)
  - [x] `finalise_analysis` chord callback
- [x] `pipeline.py` updated: inserts analysis chord between chunk_document and notify_complete
- [x] Token budget enforcement: `services/llm/token_budget.py` (per-doc 100k, per-user-day 500k, Redis cache)
- [x] Cost tracking: `estimated_cost_usd` per analysis stored in `DocumentAnalysis`
- [x] `embedding` VectorField(1536) added to `DocumentChunk` (pgvector)
- [x] Analysis API endpoints: `GET /analysis/`, `GET /analysis/clauses/`, `GET /analysis/risks/`
- [x] Write tests: task execution (mock LLM), token budget, API endpoints (auth + ownership)

**Frontend**
- [x] `types/analysis.ts` — TypeScript types for DocumentAnalysis, Clause, Risk, KeyDate
- [x] `lib/api/analysis.ts` — typed API client for analysis endpoints

---

### Sprint 5: Translation & Chat

**Backend**
- [x] `Translation` model (unique per document+language, status machine, JSON fields for translated content)
- [x] `tasks/translation.py` — translates summary, simplified text, key points, clauses, risks via LLM
- [x] `POST /api/v1/documents/{id}/translations/` — request translation (idempotent)
- [x] `GET /api/v1/documents/{id}/translations/` — list translations
- [x] `GET /api/v1/documents/{id}/translations/{lang}/` — get specific translation
- [x] `ChatSession` and `ChatMessage` models (sources JSON for RAG citations)
- [x] `ChatConsumer` — JWT-authenticated streaming WebSocket consumer
- [x] `services/rag/retrieval.py` — embed query → pgvector cosine similarity → top-4 chunks (fallback to ordered chunks)
- [x] `tasks/chat.py` — `stream_chat_response`: RAG retrieval + streaming LLM → channel_layer token pushes
- [x] `LLMProvider.stream_complete()` — added to all providers (Groq, OpenAI, Anthropic, Mock)
- [x] `POST /api/v1/documents/{id}/chat/sessions/` — start session
- [x] `GET /api/v1/documents/{id}/chat/sessions/{sid}/` — get session + all messages
- [x] `POST /api/v1/documents/{id}/chat/sessions/{sid}/messages/` — send message (enqueues stream task)
- [x] `DELETE /api/v1/documents/{id}/chat/sessions/{sid}/` — delete session
- [x] Write tests: translation pipeline, API endpoints, chat session CRUD, messaging, RAG retrieval

**Frontend**
- [x] `types/chat.ts` + `types/translation.ts`
- [x] `lib/api/chat.ts` + `lib/api/translations.ts`
- [x] `lib/hooks/useChatStream.ts` — WebSocket hook: token accumulation, stream_start/end events, reconnect
- [x] `components/chat/ChatPanel.tsx` — message list + streaming indicator + input bar
- [x] `components/chat/MessageBubble.tsx` — user/assistant bubbles + citation count + streaming cursor
- [x] `components/chat/SuggestedQuestions.tsx` — category-seeded starter questions
- [x] `/docs/[id]/chat` page — auto-creates/resumes session, full-height chat layout
- [x] `/docs/[id]/translate` page — language selector, request translation, polling, full translated content

---

## Phase 3 — UI Polish & Results (Weeks 7–9)

### Sprint 6: Results Page & Document Viewer

**Backend**
- [x] `services/export/pdf_exporter.py` — ReportLab PDF: summary, key points, simplified text, clauses, risks, dates
- [x] `POST /api/v1/documents/{id}/analysis/export/` — streams PDF as download response

**Frontend**
- [x] `components/results/RiskBadge.tsx` — severity badge (high/medium/low) with colored dot
- [x] `components/results/ClauseCard.tsx` — expandable with simplified/original toggle
- [x] `components/results/DateTimeline.tsx` — vertical timeline, past dates struck-through
- [x] `components/results/ResultsSkeleton.tsx` — animated pulse skeletons for analysis + PDF panel
- [x] `components/results/SimplifiedView.tsx` — 4-tab view: Summary | Clauses | Risks | Dates
- [x] `components/results/PDFViewer.tsx` — react-pdf with page nav + zoom controls
- [x] `components/results/DocumentLayout.tsx` — desktop split-panel (45/55) + mobile 5-tab layout
- [x] `app/docs/[id]/page.tsx` — assembles all panels; handles loading, processing, failed, done states
- [x] Export button triggers `exportAnalysis()` → blob download
- [x] Translate link → `/docs/[id]/translate`
- [x] lib/api/analysis.ts updated with `exportAnalysis()` function

---

### Sprint 7: History, Settings & Production Hardening

**Frontend**
- [ ] `/history` page: card grid sorted by date, category filter, status filter
- [ ] Search bar on history page (full-text search on filename + summary)
- [ ] `/settings` page:
  - [ ] Language preference selector
  - [ ] Password change form
  - [ ] Download all my data button
  - [ ] Delete account button (with confirmation dialog)

**Backend hardening**
- [ ] Sentry integration: `sentry-sdk[django,celery]` + DSN from env
- [ ] Structured JSON logging: `python-json-logger` — never log document content
- [ ] Celery Beat job: nightly delete expired documents from S3 + DB (after 30 days)
- [ ] Celery Beat job: reset daily upload counts (midnight UTC)
- [ ] `AuditMiddleware`: log all API requests to `audit_logs` table
- [ ] Fix all N+1 queries: `select_related` + `prefetch_related` on document list
- [ ] Redis caching of analysis results (TTL 24h)
- [ ] Load test with Locust: 50 concurrent users uploading documents
- [ ] Verify `DEBUG = False` is enforced in production settings
- [ ] Add security headers middleware: CSP, X-Frame-Options, X-Content-Type-Options
- [ ] Django QueryInspect in dev to catch remaining N+1 queries

---

## Phase 4 — Deployment (Weeks 10–12)

### Sprint 8: AWS Deployment & Full CI/CD

**AWS infrastructure**
- [ ] Create VPC with public + private subnets
- [ ] Create RDS PostgreSQL (pgvector enabled) in private subnet
- [ ] Create ElastiCache Redis in private subnet
- [ ] Create S3 bucket: private ACL, lifecycle rule (delete after 30 days), versioning off
- [ ] Create ECR registry for backend + frontend images
- [ ] Create AWS Secrets Manager secrets for all env vars
- [ ] Create ECS cluster
- [ ] Write ECS task definition: `cleardocs-api` (Django + Nginx sidecar, 1GB memory)
- [ ] Write ECS task definition: `cleardocs-worker` (Celery worker, 2GB memory)
- [ ] Write ECS task definition: `cleardocs-beat` (Celery Beat, always 1 instance)
- [ ] Configure auto-scaling for API service (CPU-based, 1–5 instances)
- [ ] Configure auto-scaling for worker service (Redis queue depth, 1–20 instances)
- [ ] Set up CloudFront distribution for Next.js static assets
- [ ] Set up Route 53 DNS + ACM SSL certificate

**CI/CD**
- [ ] Write `.github/workflows/deploy.yml`:
  - [ ] Run migrations as ECS one-off task
  - [ ] Build + push Docker images to ECR
  - [ ] Update ECS services (API + Worker)
  - [ ] `aws ecs wait services-stable`
  - [ ] Health check `/health/ready/` must return 200
  - [ ] Automatic rollback on failed health check
- [ ] Blue/green deploy: ECS deployment circuit breaker enabled

**Observability**
- [ ] CloudWatch log groups for API, Worker, Beat services
- [ ] CloudWatch dashboard: API latency p99, error rate, Celery queue depth, RDS connections
- [ ] Prometheus + Grafana for application-level metrics
- [ ] Alerts configured:
  - [ ] API error rate > 1%
  - [ ] Celery queue depth > 100
  - [ ] API p99 > 5s
  - [ ] Daily OpenAI cost > $20

---

## Security Checklist (verify before launch)

- [ ] JWT access token expiry = 15 minutes
- [ ] Refresh token in HttpOnly cookie, rotation on every use
- [ ] Email verification required before document upload
- [ ] All document endpoints check `document.user_id == request.user.id`
- [ ] ClamAV scan on every upload
- [ ] MIME type validated server-side
- [ ] 50MB file size limit enforced at Nginx + Django
- [ ] S3 bucket private — all access via signed URLs (15 min expiry)
- [ ] Files stored with UUID keys (not original filename)
- [ ] CORS restricted to specific origins
- [ ] Rate limiting active on all endpoints
- [ ] `DEBUG = False` in production
- [ ] No secrets in code or committed .env
- [ ] Audit log table has no UPDATE/DELETE permissions
- [ ] GDPR delete endpoint removes user + all documents + all analyses
- [ ] Privacy policy linked from every page
- [ ] `npm audit` + `safety check` passing in CI

---

## Bonus / Post-launch

- [ ] A/B test OpenAI vs Groq vs Anthropic on clause extraction quality
- [ ] Add AWS Textract as config-switchable OCR backend (for scanned document quality)
- [ ] Multi-document comparison view (side-by-side contract diff)
- [ ] Offline PWA support (service worker for results page)
- [ ] Browser extension: right-click any PDF link → "Explain with ClearDocs"
- [ ] Admin dashboard: user stats, processing volume, cost tracking, flagged content
- [ ] Stripe integration for optional "Pro" tier (higher daily limits)
