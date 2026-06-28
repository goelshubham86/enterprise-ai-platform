# Enterprise AI Platform

A production-grade AI Knowledge Assistant built on Google Cloud Platform, demonstrating enterprise-grade GenAI architecture using Vertex AI, FastAPI, React, Terraform, Cloud Run, LangChain, LangGraph, and Retrieval-Augmented Generation (RAG).

The platform is designed to evolve incrementally — from a document-based knowledge assistant into a fully featured AI platform supporting AI agents, Model Context Protocol (MCP), multi-agent workflows, evaluation, and production-grade observability.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                        React Frontend                          │
│         (Vite · TypeScript · Material UI · TanStack Query)     │
└────────────────────┬───────────────────────────────────────────┘
                     │ HTTPS / REST
┌────────────────────▼───────────────────────────────────────────┐
│                   FastAPI Backend (Cloud Run)                   │
│          (Python · Pydantic · LangChain · LangGraph)           │
├────────────┬───────────────────┬───────────────────────────────┤
│  Document  │   RAG / Embedding │        AI Agents              │
│  Service   │   Service         │   (LangGraph Workflows)       │
└────────────┴───────┬───────────┴───────────────────────────────┘
                     │
        ┌────────────┼────────────────┐
        │            │                │
┌───────▼──┐  ┌──────▼──────┐  ┌─────▼───────────┐
│  Cloud   │  │  Vertex AI  │  │    BigQuery      │
│ Storage  │  │  (Gemini /  │  │  (Audit Logs /   │
│  (PDFs)  │  │  Embeddings)│  │   Analytics)     │
└──────────┘  └─────────────┘  └─────────────────-┘
```

---

## Repository Structure

```
enterprise-ai-platform/
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/      # HTTP route handlers (thin layer)
│   │   │       │   ├── chat.py
│   │   │       │   ├── documents.py
│   │   │       │   └── health.py
│   │   │       └── router.py
│   │   ├── core/                   # Config, logging, security
│   │   ├── models/                 # Pydantic domain models
│   │   ├── schemas/                # Request / Response DTOs
│   │   ├── services/               # Business logic
│   │   │   ├── ai/                 # Vertex AI, embeddings, RAG
│   │   │   └── storage/            # Cloud Storage client
│   │   ├── agents/                 # LangGraph agent definitions
│   │   ├── chains/                 # LangChain chain definitions
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                       # React 19 + TypeScript + Vite
│   └── src/
│       ├── api/                    # Axios client + per-domain modules
│       ├── components/
│       │   ├── chat/               # ChatWindow, MessageBubble, ChatInput
│       │   ├── common/             # ErrorBoundary, Spinner, PageHeader
│       │   ├── documents/          # DocumentList, DocumentCard, UploadDialog
│       │   └── layout/             # AppLayout, Navbar, Sidebar
│       ├── hooks/                  # TanStack Query custom hooks
│       ├── pages/                  # Dashboard, Chat, Documents, Settings, Health
│       ├── router/                 # React Router configuration
│       ├── theme/                  # Material UI theme (Google Cloud style)
│       ├── types/                  # Shared TypeScript types
│       └── utils/                  # Formatters, constants
├── terraform/
│   ├── modules/                    # Reusable GCP resource modules
│   │   ├── cloud-run/              #   Phase 3: Cloud Run service
│   │   ├── cloud-storage/          # ✅ Phase 2: GCS bucket (production-hardened)
│   │   ├── vertex-ai/              #   Phase 5: Vertex AI Vector Search
│   │   └── networking/             #   Phase 4: VPC, subnets, serverless connector
│   ├── environments/               # Per-environment compositions
│   │   ├── dev/                    # ✅ Active — documents_bucket provisioned
│   │   ├── staging/                #   (future)
│   │   └── prod/                   #   (future)
│   ├── tests/                      # Future Terratest integration tests (Go)
│   └── .tflint.hcl                 # TFLint static analysis config
├── docs/
│   ├── architecture/               # Architecture Decision Records (ADRs)
│   ├── api/                        # OpenAPI / endpoint documentation
│   ├── deployment/                 # Deployment guides
│   └── runbooks/                   # Operational runbooks
├── cloudbuild.yaml                 # CI/CD pipeline (Cloud Build)
├── .gitignore
├── LICENSE
└── README.md
```

---

## Tech Stack

| Layer          | Technology                                              |
|----------------|---------------------------------------------------------|
| Frontend       | React 19, TypeScript, Vite, Material UI                 |
| State          | TanStack Query, React Hook Form, Zod                    |
| HTTP Client    | Axios                                                   |
| Backend        | Python 3.12, FastAPI, Pydantic v2                       |
| AI Framework   | LangChain, LangGraph                                    |
| LLM            | Vertex AI Gemini (gemini-1.5-pro)                       |
| Embeddings     | Vertex AI text-embedding-004                            |
| Vector Store   | FAISS (dev) → Vertex AI Vector Search (prod)            |
| Infrastructure | Cloud Run, Cloud Storage, Artifact Registry, Secret Mgr |
| IaC            | Terraform 1.7+                                          |
| CI/CD          | Cloud Build                                             |
| Observability  | Cloud Logging, Cloud Monitoring, Cloud Trace            |

---

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.12+
- Google Cloud SDK (`gcloud`)
- Terraform 1.7+
- TFLint ([install guide](https://github.com/terraform-linters/tflint#installation))

### Local Development

```bash
# Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev                        # http://localhost:3000

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Environment Variables

```bash
# frontend/.env.local
VITE_API_URL=http://localhost:8000

# backend/.env
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GCS_BUCKET_NAME=enterprise-ai-documents
VERTEX_MODEL_ID=gemini-1.5-pro-002
```

---

## Terraform

### Infrastructure Quality Gates

Every `terraform/**` change runs through four automated gates in Cloud Build
before a plan (and optionally an apply) is allowed:

| Step | Tool | What it checks | Credentials needed |
|------|------|----------------|--------------------|
| 1 | `terraform fmt -check` | Canonical formatting | None |
| 2 | `terraform validate` | Syntax + schema | Provider init only |
| 3 | **TFLint** | Naming, best practices, GCP rules | None |
| 4 | `terraform plan` | Full diff against state | GCP SA |

Upcoming gates (see roadmap below):

| Step | Tool | Status |
|------|------|--------|
| 5 | Terratest | Planned — after modules complete |
| 6 | Checkov | Planned — security & compliance |
| 7 | tfsec / Trivy IaC | Planned — CVE + secret scanning |
| 8 | Infracost | Planned — cost delta in PRs |

### TFLint

TFLint is configured in [`terraform/.tflint.hcl`](terraform/.tflint.hcl) with
two plugins:

- **`terraform` plugin** — naming conventions, `required_version`, deprecated
  interpolation syntax, unused declarations
- **`google` plugin** — GCP-specific rules: invalid resource names, unsupported
  regions, deprecated attributes on `google_*` resources

Neither plugin makes live API calls — both are pure HCL static analysis.

#### Install TFLint

```bash
# macOS
brew install tflint

# Linux / CI (manual)
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Verify
tflint --version
```

#### Initialize plugins (first time, and after version bumps)

```bash
cd terraform
tflint --init
```

This downloads the `google` and `terraform` plugins declared in `.tflint.hcl`
into `~/.tflint.d/plugins/`. Re-run any time you bump a plugin version.

#### Run TFLint

```bash
# Lint all modules and environments in one pass (recommended)
cd terraform
tflint --recursive

# Lint a specific directory only
tflint --chdir=terraform/modules/cloud-storage

# Compact output — one line per finding (matches Cloud Build format)
tflint --recursive --format=compact

# Show all rules being evaluated
tflint --recursive --loglevel=debug
```

#### Update plugins

```bash
# 1. Edit terraform/.tflint.hcl — bump the version field for the plugin
# 2. Re-initialise to pull the new binary
cd terraform
tflint --init

# 3. Run to verify no new findings are introduced
tflint --recursive
```

### Terratest (future)

The [`terraform/tests/`](terraform/tests/) directory is reserved for
[Terratest](https://terratest.gruntwork.io/) — Go-based integration tests that
provision real GCP resources, assert against them, and tear down. See
[`terraform/tests/README.md`](terraform/tests/README.md) for the planned test
matrix and CI integration design.

---

## Roadmap

### ✅ Phase 1 — Project Foundation
- [x] React 19 frontend with Material UI (Google Cloud Console style)
- [x] Dashboard, Chat, Documents, Settings, Health pages
- [x] FastAPI backend with versioned API (`/api/v1`)
- [x] Modular project structure (services, agents, chains, schemas)
- [x] Terraform scaffold (modules + dev/staging/prod environments)
- [x] Cloud Build CI/CD pipeline
- [x] Docker containers for Cloud Run deployment

### ⬜ Phase 2 — Document Pipeline & RAG
- [ ] PDF upload to Cloud Storage via FastAPI
- [ ] PDF parsing with PyPDF
- [ ] Text chunking (recursive character splitting)
- [ ] Embedding generation with Vertex AI text-embedding-004
- [ ] Vector store (FAISS for dev, Vertex AI Vector Search for prod)
- [ ] RAG query pipeline — retrieve chunks → augment prompt → Gemini response
- [ ] Source citations in chat responses

### ⬜ Phase 3 — LangChain Integration
- [ ] LangChain RAG chain with `RetrievalQA`
- [ ] Structured prompt templates (system + human)
- [ ] Conversation memory (`ConversationBufferMemory`)
- [ ] Streaming responses via Server-Sent Events (SSE)
- [ ] Chat session persistence

### ⬜ Phase 4 — LangGraph AI Agents
- [ ] LangGraph stateful agent graph
- [ ] Tool calling (search, calculator, document lookup)
- [ ] Agent reasoning traces visible in the UI
- [ ] Human-in-the-loop interrupts
- [ ] Multi-step task execution

### ⬜ Phase 5 — MCP & Multi-Agent Workflows
- [ ] Model Context Protocol (MCP) server integration
- [ ] Multi-agent orchestration (planner + specialist agents)
- [ ] Agent-to-agent communication via shared state graph
- [ ] Parallel agent execution with LangGraph branches

### ⬜ Phase 6 — Evaluation, Observability & Security
- [ ] RAG evaluation metrics (faithfulness, relevance, groundedness)
- [ ] LLM evaluation with Vertex AI Rapid Eval
- [ ] Distributed tracing with Cloud Trace + OpenTelemetry
- [ ] Query logging to BigQuery for analytics
- [ ] VPC Service Controls and IAP for production access
- [ ] Customer-managed encryption keys (CMEK)
- [ ] Automated security scanning in CI/CD
