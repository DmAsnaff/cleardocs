# ClearDocs — Architecture & Technology Guide

A complete, beginner-friendly explanation of how ClearDocs is built: what each
technology *is*, why it's used, and how every feature works end to end.

> **What is ClearDocs?** You upload a confusing document (a lease, a medical
> form, a government notice). ClearDocs uses AI to give you a plain-English
> summary, the key clauses explained, colour-coded risk flags, important dates,
> a Q&A chatbot that answers questions about *your* document, and a translation
> into your language.

---

## Table of contents

1. [Technology glossary — what each piece means](#1-technology-glossary--what-each-piece-means)
2. [How it all fits together (architecture)](#2-how-it-all-fits-together-architecture)
3. [The database (what we store)](#3-the-database-what-we-store)
4. [The full journey of one document](#4-the-full-journey-of-one-document)
5. [Subsystems in detail](#5-subsystems-in-detail)
6. [The frontend](#6-the-frontend)
7. [DevOps: Docker, CI/CD, AWS](#7-devops-docker-cicd-aws)
8. [Security](#8-security)
9. [Known limits & gotchas](#9-known-limits--gotchas)

---

## 1. Technology glossary — what each piece means

Read this section first. Each entry says **what it is** (plain language), **why
it exists**, and **how ClearDocs uses it**.

### Backend language & framework

**Python** — A general-purpose programming language, popular for AI/data work
because of its huge library ecosystem. The entire backend is written in Python.

**Django** — A "batteries-included" web framework for Python. A *framework* is a
pre-built skeleton for a web app so you don't write everything from scratch.
Django gives you, for free: a database layer (the ORM), user accounts, an admin
panel, security defaults, and a URL router.
→ *ClearDocs:* the whole backend (`backend/`) is a Django project.

**ORM (Object-Relational Mapper)** — A translator between Python objects and
database tables. Instead of writing SQL like `SELECT * FROM documents`, you write
`Document.objects.filter(status="done")`. It prevents SQL-injection bugs and
keeps code readable.
→ *ClearDocs:* every model in `apps/*/models.py` (User, Document, etc.).

**Migrations** — Version-controlled instructions that create/modify database
tables to match your Python models. `makemigrations` writes them; `migrate`
applies them. Think "git for your database schema."
→ *ClearDocs:* `backend/apps/*/migrations/`.

**DRF (Django REST Framework)** — An add-on to Django for building **REST APIs**.
A *REST API* is how the frontend and backend talk: the browser sends HTTP
requests (GET/POST/etc.) to URLs like `/api/v1/documents/`, and gets back JSON.
DRF handles turning database rows into JSON (*serializers*) and checking
permissions.
→ *ClearDocs:* `apps/*/serializers.py`, `apps/*/views.py`.

### Database

**PostgreSQL ("Postgres")** — A powerful open-source **relational database**. A
relational database stores data in tables with rows and columns, and enforces
relationships between them (a document *belongs to* a user).
→ *ClearDocs:* the primary datastore for users, documents, analyses, etc.

**JSONB** — A Postgres column type that stores JSON efficiently *and* lets you
query inside it. Useful when data is flexible/nested.
→ *ClearDocs:* the AI output (clauses, risks, dates) is stored as JSONB — it's
naturally list/dictionary-shaped.

**pgvector** — A Postgres extension that adds a `vector` column type and
"similarity search." This is the backbone of the chatbot (see *embeddings* and
*RAG* below).
→ *ClearDocs:* `DocumentChunk.embedding` is a 1536-number vector.

### Background jobs

**Why we need background jobs:** analysing a document (OCR + several AI calls)
can take 30–120 seconds. An HTTP request that takes that long would time out and
freeze the page. So we do it *in the background* and tell the user when it's done.

**Celery** — A "task queue" for Python: a system for running functions in the
background, outside the web request. You hand Celery a job; a separate **worker**
process picks it up and runs it.
→ *ClearDocs:* `tasks/*.py` define the jobs; a `celery_worker` container runs them.

**Redis** — A blazing-fast in-memory data store. It's a Swiss-army knife used
for many things here:
- **Message broker** for Celery (the "to-do list" workers read from).
- **Cache** (temporary storage) for rate-limit counters and daily token budgets.
- **Channel layer** for WebSockets (see below) — lets the worker push a message
  to a connected browser.
→ *ClearDocs:* one Redis container serves all three roles.

**Task chain** — Celery lets you link jobs so they run in order, each after the
previous finishes. ClearDocs' pipeline is one long chain (OCR → chunk → analyse
→ finalise).

### Real-time updates

**WebSocket** — A normal HTTP request is one-and-done (ask, get an answer,
close). A *WebSocket* is a persistent two-way connection that stays open, so the
server can *push* messages to the browser at any time (no constant re-asking).
→ *ClearDocs:* live "Extracting… Analysing… Done" progress, and streaming chat
answers word-by-word.

**WSGI vs ASGI** — These are the "plugs" between a Python web app and the web
server. **WSGI** is the old standard — it only understands regular
request/response (no WebSockets). **ASGI** is the modern async standard that
*also* handles WebSockets. If your server runs WSGI, WebSockets simply don't work.
→ *ClearDocs:* we run **ASGI** so chat and live progress work.

**Daphne** — An ASGI web server. When it's installed, Django's `runserver`
automatically uses it, enabling WebSockets in development.
→ *ClearDocs:* `daphne` in `INSTALLED_APPS`; the log shows `Starting ASGI/Daphne`.

**Django Channels** — The Django library that adds WebSocket support on top of
ASGI. A *consumer* is the WebSocket equivalent of a view (it handles a socket
connection).
→ *ClearDocs:* `apps/documents/consumers.py` (progress),
`apps/chat/consumers.py` (chat), wired in `config/asgi.py`.

### Authentication

**JWT (JSON Web Token)** — A signed token that proves who you are. After login,
the server gives the browser a token; the browser sends it with each request. The
signature means the server can trust it without a database lookup.
→ *ClearDocs:* via `djangorestframework-simplejwt`.

**Access token vs refresh token** — The **access token** is short-lived (~15 min)
and sent with every API call. The **refresh token** is long-lived and used only
to get a new access token when the old one expires.

**HttpOnly cookie** — A cookie that JavaScript *cannot* read. Storing the refresh
token here protects it from XSS (malicious scripts stealing it).
→ *ClearDocs:* access token in memory, refresh token in an HttpOnly cookie.

### Documents & AI

**OCR (Optical Character Recognition)** — Turning an *image* of text (a scanned
page) into actual selectable/searchable text.
→ *ClearDocs:* **pdfplumber** extracts text from normal PDFs (fast, free);
**pytesseract** (Google's Tesseract engine) is the fallback for scanned PDFs.

**LLM (Large Language Model)** — The AI models (like Llama, GPT, Claude) that
read and write natural language. You send a *prompt* (instructions + the
document text) and get back generated text.
→ *ClearDocs:* used for summarising, extracting clauses/risks/dates, translating,
and chatting.

**Groq / OpenAI / Anthropic** — Companies that host LLMs and expose them via an
API. **Groq** is used by default because it has a free tier.
→ *ClearDocs:* selected with the `LLM_PROVIDER` env var; the code is written so
any of them can be swapped in.

**Prompt** — The text you send an LLM: system instructions ("You are a legal
analyst… return JSON like this…") plus the user content (the document).
→ *ClearDocs:* versioned templates in `services/llm/prompts.py`.

**Token** — LLMs measure text in "tokens" (~¾ of a word). Providers bill and
rate-limit by tokens. Groq's free tier allows ~12,000 tokens/minute and
~100,000 tokens/day.
→ *ClearDocs:* `services/llm/token_budget.py` tracks usage; large docs are
analysed sequentially to stay under the per-minute limit.

**Embedding** — A list of numbers (a *vector*) that represents the *meaning* of a
piece of text. Two texts with similar meaning have vectors that are close
together. This lets a computer measure "semantic similarity" mathematically.
→ *ClearDocs:* each document chunk is embedded into a 1536-number vector stored
in pgvector.

**RAG (Retrieval-Augmented Generation)** — A technique to make an LLM answer from
*your* data instead of its training memory. Steps: (1) embed the user's question,
(2) find the most similar document chunks (retrieval), (3) put those chunks in the
prompt, (4) let the LLM answer from them (generation). This prevents
"hallucination" (making things up) and lets it cite sources.
→ *ClearDocs:* `services/rag/retrieval.py` + the chat pipeline.

**Cosine similarity** — The math used to measure how "close" two vectors (two
meanings) are. Smaller distance = more related.
→ *ClearDocs:* pgvector computes it to rank chunks for the chatbot.

### Frontend

**Next.js** — A framework built on **React** (a JavaScript library for building
user interfaces). Next.js adds routing, server-side rendering (pages arrive
pre-built for speed/SEO), and a project structure.
→ *ClearDocs:* the whole `frontend/` app.

**App Router** — Next.js's newer routing system where each folder under `app/`
is a URL. `app/upload/page.tsx` → `/upload`.

**TypeScript** — JavaScript with *types*. Types catch mistakes before the code
runs (e.g., passing a number where text is expected) and make code
self-documenting.
→ *ClearDocs:* all frontend code; types live in `frontend/types/`.

**Tailwind CSS** — A styling approach where you compose small utility classes
(`px-4`, `text-sm`, `rounded-lg`) directly in markup instead of writing separate
CSS files.

**shadcn/ui** — A set of copy-paste, accessible UI components (buttons, dialogs)
built on Radix UI and styled with Tailwind. You *own* the code, so you can
customise anything.

**Zustand** — A tiny state-management library — a shared "box" of data (like the
logged-in user) any component can read.
→ *ClearDocs:* the auth store.

**TanStack Query** — A library for fetching/caching server data with loading and
error states handled for you.

**axios** — A library for making HTTP requests from the browser. ClearDocs adds
"interceptors" that attach the JWT and auto-refresh it on expiry.

### Infrastructure

**Docker** — A tool that packages an app plus everything it needs (OS libraries,
Python, dependencies) into a portable **image**. A running copy of an image is a
**container**. It solves "works on my machine" — the container runs identically
everywhere.

**Docker Compose** — A tool to define and run *multiple* containers together
(Postgres + Redis + backend + worker + frontend…) from one `docker-compose.yml`
file, with one command.

**nginx** — A high-performance web server / reverse proxy. A *reverse proxy* sits
in front of your app and routes incoming traffic (send `/api` to Django, `/` to
the frontend) and handles rate limiting.

**GitHub Actions** — GitHub's built-in CI/CD. **CI/CD** = Continuous Integration
/ Continuous Deployment: automatically run tests on every push and (optionally)
deploy.
→ *ClearDocs:* `.github/workflows/` run tests + linting on every push.

**AWS (Amazon Web Services)** — A cloud provider. The deployment design uses:
**ECS Fargate** (run containers without managing servers), **RDS** (managed
Postgres), **ElastiCache** (managed Redis), **S3** (file storage), **CloudFront**
(CDN). *(Designed but not yet deployed.)*

**ClamAV** — An open-source antivirus engine, used to scan uploaded files before
storing them.

---

## 2. How it all fits together (architecture)

```
                         ┌─────────────────────────────┐
                         │   Browser — Next.js (:3000)  │
                         │  React UI · TypeScript · JWT │
                         └───────┬──────────────┬───────┘
                    REST (HTTP)  │              │  WebSocket (progress + chat)
                                 ▼              ▼
                    ┌────────────────────────────────────┐
                    │  Django API (:8000, ASGI / Daphne)  │
                    │  DRF views · JWT auth · Channels    │
                    └───┬───────────────┬────────────┬────┘
             writes/reads│      enqueues │            │ push events
                         ▼               ▼            │
                 ┌───────────────┐   ┌───────┐        │
                 │  PostgreSQL   │   │ Redis │◄───────┘
                 │  + pgvector   │   │broker/│
                 └───────▲───────┘   │cache/ │
                         │           │channel│
                  reads/writes       └───┬───┘
                         │               │ pulls jobs
                         │           ┌───▼──────────┐   calls    ┌──────────────┐
                         └───────────│ Celery Worker│──────────► │ Groq/OpenAI/ │
                                     │ OCR + AI jobs│            │  Anthropic   │
                                     └───┬──────────┘            └──────────────┘
                                         │ stores files
                                         ▼
                                 Local disk (dev) / S3 (prod)
```

**Why separate the worker from the API:** the API must answer fast; the worker
does the slow AI work independently and can be scaled on its own.

---

## 3. The database (what we store)

```
User ──1:many──► Document ──1:1───► DocumentAnalysis   (summary, clauses,
  │                  │                                   risks, dates as JSONB)
  │                  ├──1:many──► DocumentChunk          (text + embedding vector)
  │                  ├──1:many──► Translation            (one per language)
  │                  └──1:many──► ChatSession ──► ChatMessage
  └──────────────────────────────► AuditLog              (immutable request log)
```

- **Document.status** is a state machine: `pending → validating → extracting →
  chunking → analysing → done` (or `failed`).
- AI output is **JSONB** (flexible, queryable).
- **DocumentChunk.embedding** is the pgvector column powering chat search.

---

## 4. The full journey of one document

**Step 1 — Upload** (`apps/documents/views.py`)
The browser POSTs the file to `/api/v1/documents/`. The view validates it
(MIME type, extension, size ≤ 50MB), optionally ClamAV-scans it, saves the bytes
to storage under a random UUID name, creates a `Document` row (`status=pending`),
enqueues the pipeline, and returns `201` immediately.

**Step 2 — The Celery pipeline** (`tasks/pipeline.py`) runs in the worker:
```
validate_and_store → extract_text → chunk_document
→ generate_summary → extract_clauses → extract_risks → extract_dates
→ generate_embeddings → finalise_analysis → notify_complete
```
- **extract_text** — pdfplumber pulls the text; if a scanned PDF yields almost
  nothing, pytesseract OCR takes over.
- **chunk_document** — splits the text into overlapping pieces (`DocumentChunk`
  rows) so the AI and the chatbot can work on manageable sections.
- **the four analysis tasks** — each sends a focused prompt to the LLM and saves
  one part of `DocumentAnalysis`. **They run one at a time** to respect the
  Groq per-minute token limit, with retry/backoff on rate-limit errors, and
  tolerant JSON parsing (small models sometimes wrap JSON in markdown).
- **generate_embeddings** — turns each chunk into a vector for chat search.
- **finalise_analysis → notify_complete** — mark the document `done` and push a
  completion event.

**Step 3 — The browser follows along** (`lib/hooks/useDocumentProgress.ts`)
It opens a WebSocket for live progress **and** polls `/documents/{id}/status/`
every 2.5s as a reliable fallback. When status is `done`, it navigates to the
results page.

**Step 4 — Results** (`app/docs/[id]/page.tsx`)
Fetches the document + analysis and renders tabs: **Original** (the PDF),
**Simplified** (Summary/Clauses/Risks/Dates), **Chat**.

---

## 5. Subsystems in detail

### The LLM abstraction (`services/llm/`)
- `base.py` — an abstract `LLMProvider` interface: `complete()`,
  `stream_complete()`, `embed()`.
- `groq_provider.py`, `openai_provider.py`, `anthropic_provider.py`,
  `mock_provider.py` — concrete implementations.
- `factory.py` — reads `LLM_PROVIDER` and returns the right provider. Tests use
  `mock`, which returns canned JSON (so tests never call a real API or cost money).
- `prompts.py` — versioned prompt templates.
- `token_budget.py` — per-document and per-user-per-day token caps in Redis.

**Why this matters:** switching from Groq to OpenAI is a one-line env change —
the rest of the app doesn't know or care which provider answered.

### RAG chat (`services/rag/retrieval.py`, `tasks/chat.py`, `apps/chat/`)
1. You open a chat WebSocket and send a question.
2. The question is embedded into a vector.
3. pgvector finds the most similar document chunks (cosine similarity). If no
   embeddings exist yet, it falls back to the first chunks in order.
4. Those chunks + your question go to the LLM.
5. The answer **streams back token-by-token** over the WebSocket and cites which
   excerpts it used.

This "grounding" is the whole point: the AI answers **from your document**, not
from its training data — which is what makes it trustworthy and citable.

### Authentication (`apps/users/`)
- Register/verify email/login/refresh/logout endpoints.
- Access token in browser memory; refresh token in an HttpOnly cookie.
- `lib/api/client.ts` attaches the token to every request and, on a `401`,
  silently refreshes and retries — so the session feels uninterrupted.

### Translation (`tasks/translation.py`)
A separate background job that re-generates the analysis in a target language,
cached per `(document, language)` so re-opening is instant.

### Realtime (`config/asgi.py`, consumers)
`config/asgi.py` routes HTTP to Django and WebSockets to the Channels consumers,
authenticating the socket via a JWT passed as a query parameter.

---

## 6. The frontend

- **Routing (App Router):** `(auth)/login`, `(auth)/register`, `upload`,
  `docs/[id]`, `docs/[id]/chat`, `docs/[id]/translate`, `history`, `settings`.
- **State:** Zustand (auth), TanStack Query (server data), React Hook Form + Zod
  (form validation).
- **Components:** `upload/` (DropZone, LanguageSelector, ProgressTracker),
  `results/` (DocumentLayout, PDFViewer, SimplifiedView, ClauseCard, RiskBadge,
  DateTimeline), `chat/` (ChatPanel, MessageBubble).
- **API/hooks:** typed axios wrappers in `lib/api/`; `useDocumentProgress`,
  `useChatStream` in `lib/hooks/`.

### What each on-screen option does
| Option | What happens |
|---|---|
| **Upload** | Validates and stores the file, starts the pipeline. |
| **Simplified** | Shows the AI output: Summary, Clauses, Risks, Dates. |
| **Original** | Renders the real PDF in the browser's native viewer. |
| **Chat** | RAG Q&A grounded in your document, with citations. |
| **Translate** | Re-renders the analysis in your chosen language. |
| **Export PDF** | Server builds a clean simplified PDF (`services/export/`). |
| **History / Settings** | Past documents; language preference, data deletion. |

---

## 7. DevOps: Docker, CI/CD, AWS

- **Local:** `docker-compose.yml` defines postgres, redis, clamav, backend,
  celery_worker, celery_beat, flower (Celery dashboard), frontend, nginx. In this
  environment we run the backend in Docker and the frontend via `npm` (lighter).
- **CI:** `.github/workflows/backend.yml` (pytest + ruff + black + mypy),
  `frontend.yml` (tsc + eslint + build).
- **CD (designed):** `deploy.yml` builds images → pushes to ECR → updates ECS.
- **AWS target:** ECS Fargate (API/worker/beat), RDS Postgres, ElastiCache Redis,
  S3, CloudFront. *(Not yet provisioned.)*

---

## 8. Security

- JWT with short-lived access + rotating refresh token in an HttpOnly cookie.
- Every document endpoint checks ownership (no accessing others' documents).
- File uploads: MIME + extension + size validation, optional ClamAV scan, random
  UUID storage keys.
- CORS restricted to known origins with credentials (required for the cookie).
- Security headers (CSP, X-Frame-Options, nosniff) via middleware.
- Immutable audit log of API requests.
- No secrets in code — everything via environment variables / `.env` (gitignored).

---

## 9. Known limits & gotchas

- **Groq free tier:** ~12k tokens/min and ~100k tokens/day. Large documents are
  analysed sequentially to stay under the per-minute cap; if the daily cap is
  exhausted, some sections may be empty until it resets (midnight UTC). Upgrade
  Groq, or switch `LLM_PROVIDER`, to remove the limit. See the README
  Troubleshooting section.
- **WebSockets need ASGI/Daphne** — confirmed by `Starting ASGI/Daphne` in the
  backend log. The upload page also polls as a fallback.
- **Original-PDF preview** relies on media being served under `/media/` in dev
  with an absolute `signed_url`.
- **Embeddings on Groq** currently use a placeholder vector (Groq has no
  embedding endpoint); wiring a real embedding model (e.g. sentence-transformers
  or OpenAI embeddings) would make chat retrieval fully semantic.
