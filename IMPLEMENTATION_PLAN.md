# ClearDocs — Full Implementation Plan

**AI Document Simplifier & Multi-Language Translator**

Stack: Django · Next.js · PostgreSQL · Redis · Celery · Docker · GitHub Actions CI/CD · AWS (local-first)

Target: Senior Software Engineer portfolio project — production-grade

---

## Table of Contents

1. [Project Vision & Real-World Justification](#1-project-vision--real-world-justification)
2. [Why ClearDocs Will Stand Out — Honest Assessment](#2-why-cleardocs-will-stand-out--honest-assessment)
3. [Technology Stack — Every Choice Justified](#3-technology-stack--every-choice-justified)
4. [System Architecture](#4-system-architecture)
5. [Database Schema](#5-database-schema)
6. [API Design](#6-api-design)
7. [Document Processing Pipeline](#7-document-processing-pipeline)
8. [AI / LLM Integration Strategy](#8-ai--llm-integration-strategy)
9. [Frontend Architecture & UX Pages](#9-frontend-architecture--ux-pages)
10. [Security — Production Checklist](#10-security--production-checklist)
11. [Project Folder Structure](#11-project-folder-structure)
12. [Sprint-by-Sprint Build Plan](#12-sprint-by-sprint-build-plan)
13. [Docker & Local Dev Setup](#13-docker--local-dev-setup)
14. [CI/CD Pipeline](#14-cicd-pipeline)
15. [AWS Deployment Strategy](#15-aws-deployment-strategy)
16. [Observability & Monitoring](#16-observability--monitoring)
17. [What Separates This From Vibe-Coded Apps](#17-what-separates-this-from-vibe-coded-apps)

---

## 1. Project Vision & Real-World Justification

### The Problem

Every person on Earth will eventually receive a document they cannot fully understand — a lease agreement, a medical diagnosis report, an insurance policy, an immigration form, a terms-of-service contract, a court summons. These documents are written by lawyers for other lawyers — dense, jargon-heavy, full of clauses that can cost a person their home, health, money, or freedom if misunderstood.

Today's options are:
- **Hire a lawyer** — unaffordable for billions. A single consultation costs $200–$500/hour.
- **Ask a family member** — unreliable, they probably don't understand it either.
- **Google specific phrases** — slow, decontextualised, often leads to worse confusion.
- **Use ChatGPT** — requires the user to already know what questions to ask.

**ClearDocs solves this end-to-end.** Upload the document. Receive a plain-language explanation, highlighted key clauses, risk flags, important dates, a chatbot that answers specific questions about your document, and a full translation into your native language. Free. No ads. No account required for the first 3 documents.

### Who Benefits

- Immigrants navigating government and legal paperwork in a foreign language
- Patients trying to understand medical consent forms and discharge summaries
- First-time renters reviewing lease agreements
- Small business owners receiving vendor contracts
- Low-literacy adults who struggle with complex written language
- Anyone in a developing country without access to legal services

**Estimated addressable population: 1.5–2 billion people globally.**

---

## 2. Why ClearDocs Will Stand Out — Honest Assessment

### Where ChatGPT / generic AI tools fall short for this use case

**1. The UX friction is enormous.**
To use ChatGPT for a document, a user must: open a browser, navigate to chatgpt.com, sign in, figure out how to upload a PDF (not obvious to non-tech users), know what questions to ask (requires domain knowledge they don't have), interpret a wall of text with no structure, manually copy sections if they want to translate, repeat this every time with no history. ClearDocs does all of this in one drag-and-drop.

**2. ChatGPT gives no structured, scannable output.**
When you paste a legal document into ChatGPT, you receive a prose response. There is no "risk level: HIGH on clause 4.2", no colour-coded obligation list, no "this clause means you must pay a $500 penalty if you cancel within 30 days" highlighted in red. ClearDocs outputs structured, actionable information.

**3. There is no document memory or context persistence.**
ChatGPT (free tier) loses context across sessions. ClearDocs stores every analysis, lets users re-open documents weeks later, export a simplified PDF, and continue a Q&A session where they left off.

**4. There is no multi-document workflow.**
ClearDocs supports comparing two versions of a contract side by side. ChatGPT has no concept of "your documents".

**5. Language support is technically present in ChatGPT but experientially absent.**
ClearDocs builds the translation workflow into the first-use experience, with language selection before upload.

**6. Privacy optics.**
ClearDocs will have an explicit privacy policy: documents are processed and deleted from storage after 30 days, with a one-click "delete now" option.

### Where we are honest about limitations

- ChatGPT Plus users who are technically comfortable can largely replicate ClearDocs manually. We are not targeting them.
- The AI quality at the core is similar — we use the same underlying models (OpenAI or Anthropic API). The differentiation is entirely in the product design, workflow, and structured output.
- We are not building a legal advice tool. ClearDocs explains documents; it does not provide legal opinions.

### The real competitive moat

The moat is not the AI. The moat is:
- The **structured output format** — purpose-built for documents, not general chat
- The **workflow** — upload → process → read → ask → translate → export, all in one place
- The **accessibility-first UX** — designed for people who are not tech-savvy
- **Privacy-first positioning** — explicit data deletion, no ad targeting
- **Document history** — your documents, organised, revisitable

---

## 3. Technology Stack — Every Choice Justified

### Backend Framework: Django 5 + Django REST Framework

| Alternative | Why not chosen |
|---|---|
| FastAPI | Excellent for pure async microservices. But lacks Django's built-in ORM, admin panel, migrations system, auth, and permissions. FastAPI shines when you need maximum async throughput — we need developer productivity and a rich ecosystem. |
| Node.js / Express | JavaScript on the backend means two languages in one project. The Python AI/ML ecosystem (pdfplumber, pytesseract, LangChain, numpy) is irreplaceable for this use case. |
| Ruby on Rails | Excellent productivity, similar philosophy to Django. Rejected because the Python AI library ecosystem is the core technical advantage of this project. |

**Why Django specifically:** Django's ORM with migrations is production-battle-tested at Instagram, Pinterest, and Disqus scale. Django Admin gives a free internal operations panel. django-storages + boto3 gives S3 integration in 10 lines. djangorestframework-simplejwt gives JWT auth in 5 lines.

---

### Frontend Framework: Next.js 14 with App Router

| Alternative | Why not chosen |
|---|---|
| Plain React (Vite) | No SSR, no built-in routing, no image optimisation, no SEO support. A pure SPA would hurt discoverability. |
| Nuxt.js | Vue-based equivalent. Technically valid. Rejected because the React ecosystem has far broader hiring familiarity and better TypeScript tooling. |
| SvelteKit | Genuinely excellent. Rejected because the component library ecosystem (shadcn/ui, Radix) is React-first. |
| Remix | Strong contender. Rejected because Next.js has broader adoption and more available examples for the patterns we need. |

**Why Next.js 14 App Router specifically:** Server Components allow us to fetch document data on the server — no loading spinner on the results page. The /app directory structure maps naturally to our pages. Built-in image optimisation matters for the landing page.

---

### Database: PostgreSQL 16

| Alternative | Why not chosen |
|---|---|
| MySQL | PostgreSQL's JSONB column type is essential — we store key_clauses, risk_flags, and action_items as structured JSON that we also need to query. MySQL's JSON support is weaker. |
| MongoDB | Our data is highly relational — users have documents, documents have analyses, analyses have translations. Enforcing referential integrity in MongoDB requires application-level code that PostgreSQL handles natively. |
| SQLite | Development only. Not suitable for production concurrent writes or Celery workers accessing the database simultaneously. |

**Why PostgreSQL specifically:** JSONB with GIN indexes lets us store and query structured AI output efficiently. uuid_generate_v4() for all primary keys. Full-text search (tsvector) for document history search. Row-level security can be enabled later for multi-tenant scenarios.

---

### Task Queue: Celery 5 + Redis

| Alternative | Why not chosen |
|---|---|
| Django-Q | Significantly lower throughput, less active maintenance. |
| Dramatiq | Modern, clean API. Rejected because Celery has vastly more documentation, Stack Overflow answers, and production battle-testing. |
| RQ (Redis Queue) | Lacks Celery's task chaining (chain, chord, group) which we specifically need for the parallel pipeline. |

**Why Celery specifically:** `chain()` lets us express our pipeline declaratively. Built-in retry with exponential backoff. Flower gives a live web dashboard of all running and failed tasks. Celery Beat handles scheduled tasks (e.g., nightly S3 cleanup).

**Why Redis as broker (vs RabbitMQ):** Redis serves dual purpose — task broker AND application cache AND session store AND rate limiting backend — one infrastructure service instead of two.

---

### AI/LLM: OpenAI API (provider-abstracted)

| Alternative | Why not chosen as primary |
|---|---|
| Anthropic Claude API | Claude excels at long-context document tasks. However, OpenAI's gpt-4o has better structured JSON output reliability via `response_format: {type: "json_object"}`, which is critical for our clause extraction pipeline. We abstract the provider so Claude can be enabled as an alternative. |
| Llama 3 / Mistral (self-hosted) | Zero API cost. However, requires GPU infrastructure (~$1/hour on AWS). Hard to sustain for a free public service. |
| Google Gemini | Strong multimodal capabilities. Rejected because the Python SDK is less mature and the structured output API is less reliable. |

**For local development (free):** Use **Groq** — free, fast, OpenAI-compatible API. Change only the base URL. No credit card required. Sign up at console.groq.com.

---

### OCR: pdfplumber + pytesseract

| Alternative | Why not chosen as default |
|---|---|
| AWS Textract | Significantly better accuracy. Cost: ~$1.50 per 1,000 pages. Unsustainable at launch for a free service. Architecture is designed to swap Textract in via config flag. |
| Google Document AI | Best-in-class accuracy. Cost and privacy concerns. |

**Why pdfplumber + pytesseract:** pdfplumber extracts text from native (non-scanned) PDFs with 99%+ accuracy at zero cost. ~80% of legal/government documents are native PDFs. pytesseract (Tesseract 5) handles the scanned fallback. Total cost: $0 per document for the majority of uploads.

---

### Styling: Tailwind CSS + shadcn/ui

| Alternative | Why not chosen |
|---|---|
| Bootstrap | Creates the unmistakable look of a "Bootstrap site". The goal is a product that looks designed by a UI designer. |
| Material UI | Heavy bundle, difficult to customise, signals "Google ecosystem" which conflicts with our privacy-first positioning. |
| Chakra UI | Good developer experience. Less active development in 2024. |

**Why shadcn/ui specifically:** Not a component library — it's a collection of copy-paste components built on Radix UI primitives. Components live in your codebase — you own them and can modify every pixel. Built on Radix UI: fully accessible (ARIA), keyboard-navigable. The output looks professional and custom, not "framework-y".

---

### CI/CD: GitHub Actions

| Alternative | Why not chosen |
|---|---|
| GitLab CI | Better CI/CD native integration but requires self-hosted GitLab or paying for GitLab.com. |
| CircleCI | Excellent product. Rejected purely on cost — GitHub Actions is free for public repos. |
| Jenkins | Requires a dedicated server, manual plugin management. Overkill for a solo/small team project. |

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                        │
│          Next.js 14 (SSR + CSR, PWA-ready)              │
│        Mobile-first · Accessible · 50+ language UI      │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / WSS
┌──────────────────────▼──────────────────────────────────┐
│               DJANGO REST API GATEWAY                    │
│         JWT Auth · Rate limiting · Request routing       │
│              Nginx reverse proxy in front                │
└──────┬───────────────┬──────────────────┬───────────────┘
       │               │                  │
┌──────▼──────┐ ┌──────▼──────┐ ┌────────▼───────┐
│  Document   │ │  AI Service │ │  User Service  │
│   Service   │ │             │ │                │
│Upload/Parse │ │Simplify/Chat│ │ Auth/Profile   │
└──────┬──────┘ └──────┬──────┘ └────────────────┘
       │               │
┌──────▼───────────────▼──────────────────────────────────┐
│            CELERY TASK QUEUE (Redis broker)              │
│          OCR Worker · LLM Worker · Notify Worker         │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                   STORAGE LAYER                          │
│    PostgreSQL (primary) · Redis (cache/sessions) · S3    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│         INFRASTRUCTURE (Docker → AWS ECS)                │
│  GitHub Actions CI/CD · ECS Fargate · RDS · CloudWatch   │
└─────────────────────────────────────────────────────────┘
```

**Key Architecture Decisions:**

- **Why separate Celery workers from the Django app container:** Document processing (OCR + LLM) can take 30–120 seconds. If we ran these synchronously in the API request, the HTTP connection would time out. Workers run independently and scale independently.

- **Why Django Channels for WebSockets:** When a user uploads a document, they should see real-time progress (Extracting text... 40% → Analysing clauses... 70% → Done). Django Channels lets us push progress events from the Celery worker through Redis PubSub to the connected WebSocket client — live, push-based, no polling.

- **Why PostgreSQL JSONB for AI output:** The AI returns structured data: `{"clauses": [...], "risk_flags": [...]}`. JSONB stores it as parsed binary JSON — queries like `WHERE risk_flags @> '[{"level": "HIGH"}]'` are possible with a GIN index.

---

## 5. Database Schema

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    preferred_language VARCHAR(10) DEFAULT 'en',
    role VARCHAR(20) DEFAULT 'user', -- user | admin | moderator
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    daily_upload_count INT DEFAULT 0,
    last_upload_reset DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ -- soft delete for GDPR
);

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(500) NOT NULL,
    s3_key VARCHAR(1000) NOT NULL,
    s3_bucket VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    page_count INT,
    status VARCHAR(30) DEFAULT 'pending',
    -- pending | validating | extracting | chunking | analysing | done | failed
    doc_category VARCHAR(50), -- legal | medical | government | financial | other
    error_message TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '30 days',
    CONSTRAINT valid_status CHECK (status IN (
        'pending','validating','extracting','chunking','analysing','done','failed'
    ))
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_expires_at ON documents(expires_at);

-- Document Analysis (AI output)
CREATE TABLE document_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
    plain_language_summary TEXT,
    key_clauses JSONB,       -- [{title, original_text, plain_text, importance}]
    risk_flags JSONB,        -- [{level, description, clause_ref, recommendation}]
    important_dates JSONB,   -- [{date, description, days_until}]
    action_items JSONB,      -- [{action, deadline, party, priority}]
    parties_involved JSONB,  -- [{name, role, obligations}]
    document_type_detected VARCHAR(100),
    reading_level_score FLOAT, -- Flesch-Kincaid of original
    ai_model_used VARCHAR(100),
    prompt_version VARCHAR(20),
    total_tokens_used INT,
    estimated_cost_usd NUMERIC(10, 6),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analyses_risk ON document_analyses USING GIN(risk_flags);
CREATE INDEX idx_analyses_document_id ON document_analyses(document_id);

-- Translations
CREATE TABLE translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    target_language VARCHAR(10) NOT NULL, -- ISO 639-1 code
    translated_summary TEXT,
    translated_clauses JSONB,
    translated_risks JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    ai_model_used VARCHAR(100),
    tokens_used INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, target_language)
);

-- Chat Sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_count INT DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW()
);

-- Chat Messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user | assistant | system
    content TEXT NOT NULL,
    tokens_used INT,
    response_time_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);

-- Audit Log (immutable)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, -- nullable (unauthenticated actions)
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
```

**Django Model Notes:**
- All models inherit from a `TimeStampedModel` base with `created_at` / `updated_at`
- `Document.status` is a state machine — transitions are enforced in the service layer
- `document_analyses.key_clauses` and similar JSONB fields use `django.db.models.JSONField`
- Soft-delete on users table only — documents are hard-deleted to comply with GDPR "right to erasure"

---

## 6. API Design

**Base URL:** `https://api.cleardocs.app/api/v1/`

**Standard response envelope:**
```json
{
    "status": "success" | "error",
    "data": { ... },
    "message": "Human-readable message",
    "errors": { "field": ["error detail"] }
}
```

### Endpoints

**Auth**
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register/` | Register with email + password |
| POST | `/api/v1/auth/login/` | Returns access + refresh tokens |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token |
| POST | `/api/v1/auth/logout/` | Blacklist refresh token |
| POST | `/api/v1/auth/verify-email/` | Verify email with token |
| POST | `/api/v1/auth/password-reset/` | Request password reset |
| POST | `/api/v1/auth/password-reset/confirm/` | Confirm password reset |
| GET | `/api/v1/auth/me/` | Current user profile |
| PATCH | `/api/v1/auth/me/` | Update profile / preferred language |
| DELETE | `/api/v1/auth/me/` | GDPR delete account + all data |

**Documents**
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents/` | Upload document (multipart) |
| GET | `/api/v1/documents/` | List user's documents (paginated) |
| GET | `/api/v1/documents/{id}/` | Get document + processing status |
| DELETE | `/api/v1/documents/{id}/` | Delete document + S3 file + analysis |
| GET | `/api/v1/documents/{id}/status/` | Lightweight status poll (backup to WS) |

**Analysis**
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/documents/{id}/analysis/` | Full analysis result |
| GET | `/api/v1/documents/{id}/analysis/summary/` | Plain language summary only |
| GET | `/api/v1/documents/{id}/analysis/clauses/` | Key clauses only |
| GET | `/api/v1/documents/{id}/analysis/risks/` | Risk flags only |
| POST | `/api/v1/documents/{id}/analysis/export/` | Export simplified PDF |

**Translations**
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents/{id}/translations/` | Request translation to language |
| GET | `/api/v1/documents/{id}/translations/` | List available translations |
| GET | `/api/v1/documents/{id}/translations/{lang}/` | Get specific translation |

**Chat**
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents/{id}/chat/sessions/` | Start chat session |
| GET | `/api/v1/documents/{id}/chat/sessions/{sid}/` | Get session messages |
| POST | `/api/v1/documents/{id}/chat/sessions/{sid}/messages/` | Send message |
| DELETE | `/api/v1/documents/{id}/chat/sessions/{sid}/` | Delete session |

**WebSocket**
| Endpoint | Description |
|---|---|
| `WS /ws/documents/{id}/progress/` | Real-time processing progress |
| `WS /ws/chat/{session_id}/` | Real-time chat streaming |

**Health**
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health/` | Shallow check (always 200 if server is up) |
| GET | `/health/ready/` | Deep check (DB + Redis + S3 connectivity) |

### Rate Limiting

| Endpoint | Limit |
|---|---|
| `POST /auth/login/` | 5 requests / minute / IP |
| `POST /documents/` | 5 uploads / day / user (free tier) |
| `POST /chat/messages/` | 30 messages / hour / user |
| All other endpoints | 120 requests / minute / user |

---

## 7. Document Processing Pipeline

### State Machine
```
PENDING → VALIDATING → EXTRACTING → CHUNKING → ANALYSING → DONE
                                                          ↘ FAILED
```

### Celery Task Chain
```python
# tasks/pipeline.py
from celery import chain, group

def process_document(document_id: str):
    pipeline = chain(
        validate_and_store.s(document_id),
        extract_text.s(),
        chunk_document.s(),
        group(
            generate_summary.s(),
            extract_clauses.s(),
            extract_risks.s(),
            extract_dates.s(),
        ),
        finalise_analysis.s(),
        notify_user.s(),
    )
    pipeline.apply_async()
```

### Step 1: Validate & Store
- Check MIME type is in allowed list (application/pdf, .docx, image/jpeg, image/png)
- Run ClamAV virus scan (clamd daemon in Docker)
- Upload to S3 with server-side encryption (AES256)
- Generate signed URL for downstream workers to retrieve the file
- Update status to `VALIDATING`

### Step 2: Text Extraction
```python
def extract_text(document_id: str) -> str:
    doc = Document.objects.get(id=document_id)
    file_bytes = s3_client.download(doc.s3_key)
    if doc.mime_type == 'application/pdf':
        text = extract_pdf_text(file_bytes)   # pdfplumber
        if len(text.strip()) < 100:
            text = ocr_pdf(file_bytes)        # pytesseract fallback
    elif doc.mime_type.startswith('image/'):
        text = ocr_image(file_bytes)          # pytesseract
    elif 'wordprocessingml' in doc.mime_type:
        text = extract_docx_text(file_bytes)  # python-docx
    doc.extracted_text = text
    doc.status = 'chunking'
    doc.save()
    return document_id
```

### Step 3: Semantic Chunking
Chunk by semantic boundaries (section headers, paragraph breaks, Q&A blocks), not naive character count:
- Max 3,000 tokens per chunk (leave room for system prompt)
- 200-token overlap between chunks for context continuity
- Split priority: section → paragraph → sentence

### Step 4: Parallel AI Analysis

**Simplification prompt:**
```
You are helping a person with no legal or medical training understand a document.
Rewrite the following section in plain English at a reading level of Grade 6 (age 11-12).
Do not omit important information. Preserve all numbers, dates, names, and obligations exactly.
Output valid JSON: {"simplified": "...", "reading_level": 6}
```

**Clause extraction prompt:**
```
Extract all key clauses from the following document section.
For each clause output: title, original_text, plain_text, importance (critical|high|medium|low),
type (obligation|deadline|penalty|right|restriction|definition), party_affected.
Output: {"clauses": [...]}
```

**Risk extraction prompt:**
```
Identify potential risks, unfair terms, unusual clauses, or obligations the reader should be aware of.
Focus on: automatic renewals, penalty clauses, unilateral change rights, liability waivers,
data sharing clauses, unusual termination conditions.
Output: {"risks": [{"level": "high|medium|low", "description": "...", "recommendation": "..."}]}
```

### Step 5: Result Finalisation
- Merge all chunk analyses into a single `DocumentAnalysis` record
- Deduplicate overlapping clauses from chunk boundaries
- Sort risk flags by severity (HIGH → MEDIUM → LOW)
- Calculate `reading_level_score` for the original document (Flesch-Kincaid)
- Update document status to `done`
- Push WebSocket event to connected client

---

## 8. AI / LLM Integration Strategy

### Provider Abstraction
```python
# services/llm/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResponse:
    content: str
    tokens_used: int
    model: str
    cost_usd: float

class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, response_format: dict) -> LLMResponse:
        pass

    @abstractmethod
    def stream(self, system: str, user: str):
        pass
```

### Token Budgeting
```python
MAX_TOKENS_PER_DOCUMENT = 100_000      # ~$0.10 at gpt-4o-mini pricing
MAX_TOKENS_PER_USER_PER_DAY = 500_000

def check_token_budget(user_id: str, estimated_tokens: int):
    today_usage = cache.get(f'tokens:{user_id}:{today}', 0)
    if today_usage + estimated_tokens > MAX_TOKENS_PER_USER_PER_DAY:
        raise TokenBudgetExceeded("Daily limit reached")
```

### Chat RAG Architecture
For the document Q&A feature:
1. At analysis time, chunk text is embedded using `text-embedding-3-small` and stored in PostgreSQL with `pgvector` extension
2. On each chat message, the user's question is embedded
3. Top-3 most semantically relevant chunks are retrieved via cosine similarity
4. These chunks are injected as context into the LLM prompt
5. The LLM answers from the retrieved context — with citations

This prevents hallucination on document-specific questions. The LLM is grounded in the actual document text, not its training data.

### Prompt Versioning
Every LLM prompt is stored as a versioned template in `services/llm/prompts.py`. The prompt version used for each analysis is recorded in `document_analyses.prompt_version`. This lets us audit why older analyses look different from newer ones and run controlled A/B experiments on prompts.

---

## 9. Frontend Architecture & UX Pages

### Page Structure (Next.js App Router)
| Route | Description |
|---|---|
| `/` | Landing page (public, SSR, SEO-optimised) |
| `/register` | Sign up |
| `/login` | Sign in |
| `/upload` | Document upload (auth required) |
| `/docs/[id]` | Document results (auth required) |
| `/docs/[id]/translate` | Translation view |
| `/docs/[id]/chat` | Q&A chatbot |
| `/history` | Past documents |
| `/settings` | Account settings, language preference, data deletion |
| `/about` | About, privacy policy, disclaimer |

### Landing Page
- Headline speaks to the pain, not the feature: **"Understand any document in plain English"**
- Single CTA: "Upload a document — it's free"
- Three example use cases with before/after: legal contract → simplified version
- Language selector in the top nav — the landing page itself translates to the user's selected language
- No cookie banner (no tracking cookies, no ads)

### Upload Page
- Drag-and-drop zone is the hero — full viewport height on mobile
- Language dropdown: "Explain this document in [English ▼]" — default to browser language
- Category selector (optional): Legal / Medical / Government / Financial / Other
- Privacy badge: "Your document is processed securely and deleted after 30 days"
- Animated progress indicator with stage labels via WebSocket
- No upload button — processing starts immediately on file drop

### Results Page (most critical)
- Split-panel layout on desktop: original document (PDF viewer, left 45%) + simplified explanation (right 55%)
- On mobile: tabs — "Original" | "Simplified" | "Clauses" | "Chat"
- Risk flags are the first thing visible above the fold — colour-coded cards (red/amber/green)
- Clause cards are expandable: show plain-text summary, click to see original clause
- "Important dates" section: timeline view of deadlines and renewal dates
- Sticky top bar: document name, language selector, export button
- "Ask a question" chat panel slides in from the right on desktop, full-screen on mobile

### Chat Page
- Persistent chat history for the document session
- Suggested starter questions based on document category
- Citations: each AI answer includes "Source: Page 3, Section 4.2" reference
- Character-by-character streaming response (SSE from Django Channels)

### Mobile-First Considerations
- Minimum tap target: 44×44px on all interactive elements
- Bottom navigation bar on mobile (no hamburger menu)
- PDF viewer is replaced by the simplified view on mobile by default
- Upload supports camera capture on mobile
- All text is minimum 16px to prevent iOS auto-zoom on inputs
- Tested on Chrome Android, Safari iOS, Firefox Android

---

## 10. Security — Production Checklist

### Authentication & Authorisation
- [ ] JWT access tokens: 15-minute expiry. Refresh tokens: 7 days, stored in HttpOnly cookie (not localStorage)
- [ ] Refresh token rotation on every use — compromised token cannot be reused
- [ ] Email verification required before document upload
- [ ] All document endpoints verify `document.user_id == request.user.id` — no IDOR
- [ ] Admin endpoints behind `is_staff` check + IP allowlist in staging/prod

### File Upload Security
- [ ] ClamAV virus scan on every upload before S3 storage
- [ ] MIME type validation server-side (never trust Content-Type header)
- [ ] File extension allowlist: .pdf, .docx, .jpg, .jpeg, .png
- [ ] Maximum file size: 50MB enforced at Nginx and Django layers
- [ ] S3 bucket is private — all access via signed URLs (15-minute expiry)
- [ ] Files stored with UUID keys — original filename never used as S3 key

### API Security
- [ ] CORS configured to specific allowed origins only
- [ ] CSRF protection enabled for cookie-based endpoints
- [ ] SQL injection impossible — Django ORM parameterises all queries
- [ ] All user input sanitised before AI prompt injection (prompt injection defence)
- [ ] Rate limiting at Nginx (connection-level) and Django (application-level, Redis-backed)
- [ ] Sensitive fields (hashed_password, s3_key) never serialised in API responses
- [ ] `DEBUG = False` in all non-development environments

### Infrastructure Security
- [ ] Secrets in AWS Secrets Manager — never in code, never in .env committed to git
- [ ] Database not publicly accessible — only reachable from ECS VPC
- [ ] Redis not publicly accessible — only reachable from application containers
- [ ] SSL/TLS enforced on all endpoints (HTTPS redirect, HSTS header)
- [ ] Security headers: `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`
- [ ] Dependency vulnerability scanning in CI pipeline

### Privacy & Compliance
- [ ] Documents hard-deleted from S3 and PostgreSQL after 30 days (Celery Beat job)
- [ ] One-click "delete all my data" endpoint — removes user + all documents + all analyses
- [ ] No document content written to application logs
- [ ] Audit log is immutable (no UPDATE/DELETE permissions on audit_logs table)
- [ ] GDPR-compliant privacy policy linked from every page

---

## 11. Project Folder Structure

```
cleardocs/
├── .github/
│   └── workflows/
│       ├── backend.yml          # Django test + lint + build
│       ├── frontend.yml         # Next.js test + lint + build
│       └── deploy.yml           # Deploy to ECS on merge to main
│
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py          # Shared settings
│   │   │   ├── development.py   # Local overrides
│   │   │   ├── staging.py
│   │   │   └── production.py   # Production-hardened
│   │   ├── urls.py
│   │   ├── asgi.py              # Channels ASGI config
│   │   └── celery.py            # Celery app init
│   │
│   ├── apps/
│   │   ├── users/
│   │   │   ├── models.py        # CustomUser model
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── tests/
│   │   ├── documents/
│   │   │   ├── models.py        # Document, DocumentChunk
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── validators.py    # File type, size validation
│   │   │   └── tests/
│   │   ├── analysis/
│   │   │   ├── models.py        # DocumentAnalysis
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── tests/
│   │   ├── translations/
│   │   │   ├── models.py        # Translation
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── tests/
│   │   ├── chat/
│   │   │   ├── models.py        # ChatSession, ChatMessage
│   │   │   ├── consumers.py     # Django Channels WebSocket consumer
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── tests/
│   │   └── audit/
│   │       ├── models.py        # AuditLog
│   │       ├── middleware.py    # Auto-log all API calls
│   │       └── tests/
│   │
│   ├── services/
│   │   ├── llm/
│   │   │   ├── base.py          # LLMProvider ABC
│   │   │   ├── openai_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   ├── prompts.py       # All prompt templates (versioned)
│   │   │   └── rag.py           # RAG retrieval for chat
│   │   ├── ocr/
│   │   │   ├── extractor.py     # pdfplumber + pytesseract
│   │   │   └── chunker.py       # Semantic chunking
│   │   ├── storage/
│   │   │   ├── s3_client.py     # boto3 wrapper
│   │   │   └── antivirus.py     # ClamAV client
│   │   └── export/
│   │       └── pdf_exporter.py  # ReportLab simplified PDF export
│   │
│   ├── tasks/
│   │   ├── pipeline.py          # Main Celery task chain
│   │   ├── analysis.py          # LLM analysis tasks
│   │   ├── ocr.py               # Text extraction tasks
│   │   ├── notifications.py     # Email + WebSocket notify tasks
│   │   └── maintenance.py       # Celery Beat scheduled jobs
│   │
│   ├── tests/
│   │   ├── conftest.py          # pytest fixtures
│   │   ├── factories.py         # factory_boy model factories
│   │   └── integration/         # End-to-end pipeline tests
│   │
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   │
│   ├── Dockerfile
│   └── manage.py
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx            # Root layout, fonts, metadata
│   │   ├── page.tsx              # Landing page (/)
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── upload/
│   │   │   └── page.tsx
│   │   ├── docs/
│   │   │   └── [id]/
│   │   │       ├── page.tsx      # Results page
│   │   │       ├── chat/page.tsx
│   │   │       └── translate/page.tsx
│   │   ├── history/
│   │   │   └── page.tsx
│   │   └── settings/
│   │       └── page.tsx
│   │
│   ├── components/
│   │   ├── upload/
│   │   │   ├── DropZone.tsx
│   │   │   ├── LanguageSelector.tsx
│   │   │   ├── CategorySelector.tsx
│   │   │   └── ProgressTracker.tsx   # WebSocket progress UI
│   │   ├── viewer/
│   │   │   ├── DocumentLayout.tsx    # Split-panel layout
│   │   │   ├── PDFViewer.tsx         # react-pdf wrapper
│   │   │   ├── SimplifiedView.tsx    # Rendered analysis
│   │   │   ├── ClauseCard.tsx
│   │   │   ├── RiskBadge.tsx
│   │   │   └── DateTimeline.tsx
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── SuggestedQuestions.tsx
│   │   └── ui/                       # shadcn/ui components
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts             # Axios instance with JWT interceptors
│   │   │   ├── documents.ts
│   │   │   ├── auth.ts
│   │   │   └── chat.ts
│   │   ├── hooks/
│   │   │   ├── useDocumentProgress.ts  # WebSocket hook
│   │   │   ├── useDocumentAnalysis.ts  # TanStack Query hook
│   │   │   └── useAuth.ts
│   │   ├── stores/
│   │   │   └── authStore.ts          # Zustand auth state
│   │   └── utils/
│   │       ├── langUtils.ts
│   │       └── dateUtils.ts
│   │
│   ├── types/
│   │   ├── document.ts
│   │   ├── analysis.ts
│   │   └── user.ts
│   │
│   ├── messages/                     # next-intl translation files
│   │   ├── en.json
│   │   └── es.json
│   │
│   ├── public/
│   ├── Dockerfile
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile
│
├── infrastructure/
│   ├── docker-compose.yml            # Local full stack
│   ├── docker-compose.test.yml       # CI test stack
│   └── aws/
│       ├── ecs-task-definition-api.json
│       ├── ecs-task-definition-worker.json
│       └── cloudwatch-dashboard.json
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONTRIBUTING.md
│   ├── DEPLOYMENT.md
│   └── ADR/
│       ├── 001-django-over-fastapi.md
│       └── 002-celery-over-django-q.md
│
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

---

## 12. Sprint-by-Sprint Build Plan

### Phase 1 — Foundation (Weeks 1–2)

#### Sprint 1: Project Scaffolding & Infrastructure (Week 1–2)
**Goal:** Any engineer can clone the repo and run the full stack with `docker compose up`

- Initialise monorepo with `backend/` and `frontend/` directories
- Django project setup: `django-admin startproject config .`
- Install and configure: DRF, simplejwt, django-storages, django-channels, celery, redis, psycopg2
- Next.js 14 setup: `create-next-app@latest --typescript --tailwind --app`
- Install shadcn/ui: `npx shadcn-ui@latest init`
- Docker Compose with all services: postgres, redis, backend, celery worker, celery beat, flower, frontend, nginx
- `.env.example` with all required variables documented
- GitHub Actions: `backend.yml` (pytest + ruff + black), `frontend.yml` (jest + eslint + tsc)
- Pre-commit hooks: ruff, black, mypy, eslint, prettier
- README.md with full local setup instructions

**Deliverable:** `docker compose up` starts all services. GitHub Actions runs green on every push.

#### Sprint 2: Authentication System (Week 2)
**Goal:** Users can register, verify email, login, and receive a JWT

Backend:
- Custom User model extending `AbstractBaseUser`
- Register endpoint with email uniqueness check
- Email verification: generate signed token, send via django-anymail (Mailgun/SES)
- Login endpoint returning access + refresh tokens
- Refresh token endpoint
- Logout endpoint (blacklist refresh token)
- Profile GET/PATCH endpoint
- Account deletion endpoint (soft-delete + cascade)
- Rate limiting on login endpoint (5 attempts/min)
- Tests: register, login, refresh, logout, email verification, rate limiting

Frontend:
- Register page with RHF + Zod validation
- Login page with JWT storage in memory (access) + HttpOnly cookie (refresh)
- Axios interceptors: attach access token, auto-refresh on 401
- Zustand auth store: `{ user, isAuthenticated, login, logout }`
- Protected route wrapper component
- Email verification landing page

---

### Phase 2 — Core Features (Weeks 3–6)

#### Sprint 3: Document Upload & Pipeline Foundation (Weeks 3–4)
**Goal:** User can upload a PDF and see it stored + queued for processing

Backend:
- Document and DocumentChunk models with migrations
- Upload endpoint: validate MIME, run ClamAV, upload to S3, create DB record, queue Celery task
- `extract_text` Celery task: pdfplumber → pytesseract fallback
- `chunk_document` Celery task: semantic splitting
- Document status endpoint (for polling backup)
- Django Channels setup: ASGI_APPLICATION, Redis channel layer, routing
- `DocumentProgressConsumer`: WebSocket consumer that listens to Redis PubSub and forwards to client
- S3 signed URL generation for document retrieval
- Tests: upload, validation rejection, text extraction, chunking, WebSocket progress

Frontend:
- DropZone component: react-dropzone, file type validation, size limit display
- Language selector (ISO 639-1 list, browser language default)
- Category selector (Legal / Medical / Government / Financial / Other)
- `useDocumentProgress` hook: WebSocket connection, progress state management
- ProgressTracker component: animated stages display
- Upload page assembled with all components

#### Sprint 4: AI Analysis Engine (Weeks 4–5)
**Goal:** Uploaded documents are fully analysed by the LLM pipeline

Backend:
- `LLMProvider` ABC and `OpenAIProvider` implementation
- Prompt templates for: simplification, clause extraction, risk extraction, date extraction
- `DocumentAnalysis` model with migrations
- Parallel Celery group: generate_summary + extract_clauses + extract_risks + extract_dates
- `finalise_analysis` task: merge results, deduplicate, calculate reading level
- `notify_user` task: push WebSocket event + send email
- Token budget enforcement per document and per user per day
- Cost tracking: log `estimated_cost_usd` per analysis
- pgvector extension + `DocumentChunk.embedding` field for RAG
- Embedding task: compute and store embeddings for all chunks after analysis
- Tests: full pipeline with mocked LLM, token budget enforcement

#### Sprint 5: Translation & Chat (Weeks 5–6)
**Goal:** Users can translate a document and ask questions about it

Backend:
- Translation model with migrations
- Translation Celery task: translate summary + clauses to requested language
- Translation API endpoints (request, list, retrieve)
- `ChatSession` and `ChatMessage` models
- `ChatConsumer`: Django Channels WebSocket consumer for streaming chat
- RAG retrieval: embed question → cosine similarity → top-3 chunks → LLM prompt
- Streaming response: stream LLM tokens to WebSocket client
- Tests: translation pipeline, chat session creation, RAG retrieval, streaming

Frontend:
- `ChatPanel` component: message list, input, send button
- `MessageBubble` with citation display
- `SuggestedQuestions` seeded by document category
- Translation view: full translated document in selected language
- Language switcher on results page

---

### Phase 3 — UI Polish & Results (Weeks 7–9)

#### Sprint 6: Results Page & Document Viewer (Weeks 7–8)
**Goal:** The results page is complete, polished, and mobile-responsive

Frontend:
- Split-panel desktop layout: `DocumentLayout` component
- PDFViewer with react-pdf: page navigation, zoom, scroll sync with simplified view
- `SimplifiedView`: full structured rendering of `DocumentAnalysis`
- `RiskBadge` component: HIGH (red), MEDIUM (amber), LOW (green), with tooltip
- `ClauseCard`: expandable, shows plain text + original on click
- `DateTimeline`: horizontal timeline of important dates
- Mobile layout: tab-based (Original / Simplified / Clauses / Chat)
- Export button: download simplified analysis as PDF (`/analysis/export/`)
- Loading skeleton for all sections while processing

#### Sprint 7: History, Settings & Production Hardening (Week 9)

Frontend:
- History page: card grid, search, filter, delete
- Settings page: language preference, password change, download all data, delete account

Backend hardening:
- Sentry integration: `sentry-sdk[django,celery]`
- Structured JSON logging: `python-json-logger`
- Celery Beat job: delete expired documents from S3 and DB (nightly)
- Celery Beat job: reset daily upload counts (midnight UTC)
- `AuditMiddleware`: log all API requests to `audit_logs`
- Performance: `select_related` and `prefetch_related` on all N+1-prone queries
- Cache analysis results in Redis (TTL 24h)
- Load test with Locust: 50 concurrent users uploading documents

---

### Phase 4 — Deployment (Weeks 10–12)

#### Sprint 8: AWS Deployment & Full CI/CD

- Create AWS resources: VPC, RDS PostgreSQL, ElastiCache Redis, S3 bucket, ECR registry
- ECS Fargate task definitions: API (Django + Nginx), Worker (Celery), Beat (Celery scheduler)
- ECS service auto-scaling: scale workers based on Redis queue depth
- AWS Secrets Manager: all secrets referenced in task definition
- CloudFront distribution for Next.js static assets
- Route 53 + ACM SSL certificate for custom domain
- GitHub Actions `deploy.yml`: test → build → push ECR → update ECS service → health check
- Blue/green deploy: ECS deployment circuit breaker + automatic rollback on failed health checks
- CloudWatch dashboards: API latency, error rate, Celery queue depth, RDS connections
- Prometheus + Grafana for application-level metrics
- Alerts for: error rate > 1%, queue depth > 100, API p99 > 5s

---

## 13. Docker & Local Dev Setup

```yaml
# docker-compose.yml
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: cleardocs
      POSTGRES_USER: cleardocs
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cleardocs"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  clamav:
    image: clamav/clamav:stable
    volumes:
      - clamav_data:/var/lib/clamav
    ports:
      - "3310:3310"

  backend:
    build:
      context: ./backend
      target: development
    command: python manage.py runserver 0.0.0.0:8000
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
      DATABASE_URL: postgresql://cleardocs:${POSTGRES_PASSWORD}@postgres:5432/cleardocs
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_S3_BUCKET: ${AWS_S3_BUCKET}
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build:
      context: ./backend
      target: development
    command: celery -A config worker --loglevel=info --concurrency=2 -Q default,ocr,llm
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
      DATABASE_URL: postgresql://cleardocs:${POSTGRES_PASSWORD}@postgres:5432/cleardocs
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      - backend
      - redis

  celery_beat:
    build:
      context: ./backend
      target: development
    command: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./backend:/app
    depends_on:
      - backend
      - redis

  flower:
    image: mher/flower
    command: celery flower --broker=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - redis

  frontend:
    build:
      context: ./frontend
      target: development
    command: npm run dev
    environment:
      NEXT_PUBLIC_API_URL: http://localhost/api/v1
      NEXT_PUBLIC_WS_URL: ws://localhost/ws
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"

  nginx:
    build:
      context: ./nginx
    ports:
      - "80:80"
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  clamav_data:
```

### Local Setup Commands
```bash
# 1. Clone and setup
git clone https://github.com/yourusername/cleardocs.git
cd cleardocs
cp .env.example .env    # Edit with your Groq/OpenAI key

# 2. Start all services
docker compose up -d

# 3. Run migrations
docker compose exec backend python manage.py migrate

# 4. Create superuser (for Django Admin)
docker compose exec backend python manage.py createsuperuser

# 5. Access services
# Frontend:     http://localhost
# Django Admin: http://localhost/admin
# API:          http://localhost/api/v1/
# Flower:       http://localhost:5555
# API Docs:     http://localhost/api/v1/schema/swagger/
```

---

## 14. CI/CD Pipeline

```yaml
# .github/workflows/backend.yml
name: Backend CI
on:
  push:
    paths: ['backend/**']
  pull_request:
    paths: ['backend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: test_cleardocs
          POSTGRES_USER: cleardocs
          POSTGRES_PASSWORD: testpassword
      redis:
        image: redis:7-alpine
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - name: Install dependencies
        run: pip install -r backend/requirements/development.txt
      - name: Lint (ruff)
        run: ruff check backend/
      - name: Format check (black)
        run: black --check backend/
      - name: Type check (mypy)
        run: mypy backend/
      - name: Run tests
        env:
          DATABASE_URL: postgresql://cleardocs:testpassword@localhost/test_cleardocs
          REDIS_URL: redis://localhost:6379/0
          DJANGO_SETTINGS_MODULE: config.settings.test
        run: |
          cd backend
          pytest --cov=. --cov-report=xml --cov-fail-under=80
```

---

## 15. AWS Deployment Strategy

### Services Used

| Service | Purpose | Local equivalent |
|---|---|---|
| ECS Fargate | Run Docker containers without managing EC2 | Docker Compose |
| RDS PostgreSQL | Managed PostgreSQL with automated backups | postgres container |
| ElastiCache Redis | Managed Redis with replication | redis container |
| S3 | Document file storage | LocalStack / MinIO |
| ECR | Docker image registry | Local Docker |
| CloudFront | CDN for Next.js static files | nginx |
| Route 53 | DNS management | /etc/hosts |
| ACM | Free SSL certificates | Local self-signed |
| Secrets Manager | Environment variable secrets | .env file |
| CloudWatch | Logs and metrics | Console output |

### ECS Task Definitions (3 separate, separate scaling policies)
- **cleardocs-api** — Django + Nginx sidecar. Scale: 1–5 instances based on CPU. Memory: 1GB.
- **cleardocs-worker** — Celery worker. Scale: 1–20 instances based on Redis queue depth. Memory: 2GB.
- **cleardocs-beat** — Celery Beat scheduler. Always exactly 1 instance.

### Cost Estimate (~1,000 users/day)

| Service | Monthly cost |
|---|---|
| ECS Fargate (API, 1 instance) | ~$15 |
| ECS Fargate (Worker, avg 2 instances) | ~$30 |
| RDS t3.micro PostgreSQL | ~$15 |
| ElastiCache t3.micro Redis | ~$15 |
| S3 (10GB storage + requests) | ~$3 |
| CloudFront | ~$2 |
| OpenAI API (1,000 docs × ~$0.05/doc) | ~$50 |
| **Total** | **~$130/month** |

---

## 16. Observability & Monitoring

### Logging Strategy
All application logs are structured JSON. Never log: document content, extracted text, S3 keys, email addresses, JWT tokens.

### Key Metrics to Track

| Metric | Alert threshold | Why |
|---|---|---|
| API p99 latency | > 3s | User experience |
| API error rate (5xx) | > 0.5% | Service health |
| Celery queue depth (LLM queue) | > 50 | Worker scale-out needed |
| Document processing time (p95) | > 120s | Pipeline performance |
| LLM API error rate | > 2% | Provider issue |
| Daily API cost (OpenAI) | > $20 | Cost control |
| DB connection pool usage | > 80% | DB capacity |

---

## 17. What Separates This From Vibe-Coded Apps

1. **Idempotent Task Pipeline** — Every Celery task can be safely re-run. If the LLM worker crashes mid-analysis, the task retries from the beginning of that stage. The document state machine prevents double-processing.

2. **State Machine Enforcement** — `Document.status` follows a strict state machine. Invalid transitions (e.g., `done → extracting`) are rejected at the service layer.

3. **Zero-Downtime Database Migrations** — Never drop columns in a single migration. Pattern: (1) add nullable column, (2) deploy code writing to both, (3) backfill, (4) drop old column in a separate deploy.

4. **Provider-Agnostic LLM Layer** — The LLM client is behind an abstract interface. Switch from OpenAI to Anthropic by changing one environment variable.

5. **Token Budget Enforcement** — Before sending any document to the LLM, estimate the token count and check against per-document and per-user-per-day budgets. Prevents runaway costs from malicious uploads.

6. **Prompt Versioning** — Every LLM prompt is a versioned template. The prompt version used for each analysis is recorded in the database. Enables A/B testing and auditability.

7. **Cursor-Based Pagination** — Document history uses cursor-based pagination, not offset pagination. Stable when new uploads occur between page requests.

8. **Signed S3 URLs with Short Expiry** — Documents are never publicly accessible. Workers and frontend receive separate 15-minute signed URLs. Cannot be shared or intercepted.

9. **Architecture Decision Records** — `docs/ADR/` contains written explanations of why each major technology was chosen. A senior engineering practice for future team members.

10. **Tests That Actually Test Behaviour** — Tests use `factory_boy` for realistic test data. The LLM is mocked — we test that the pipeline calls the LLM with the correct structure. The pipeline integration test uploads a real PDF and asserts `document.status == 'done'` and `analysis.key_clauses` is a non-empty list.

---

*Document version: 1.0 — Stack: Django 5 · Next.js 14 · PostgreSQL 16 · Redis 7 · Celery 5 · Docker · GitHub Actions · AWS ECS*
