<div align="center">

# ✦ Project Insight

**An AI briefing engine that fights information overload — not feeds it.**

Pulls thousands of words from your subscriptions, runs them through a 4-node multi-agent pipeline, and delivers exactly **5–10 insight cards per day**. When you're done reading, it says so. Then it stops.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-FF6B35?style=flat-square)](https://github.com/langchain-ai/langgraph)
[![Kotlin](https://img.shields.io/badge/Kotlin-Compose-7F52FF?style=flat-square&logo=kotlin&logoColor=white)](https://kotlinlang.org)
[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-D97706?style=flat-square)](https://claude.ai/code)

</div>

---

## The Problem

Modern feeds are engineered to trap you. Every scroll reveals more content, every notification pulls you back. The result: you read for hours and retain nothing.

Insight is built on the opposite philosophy — **information closure**. A fixed daily output. No infinite scroll. No red dots. When you've read today's cards, the app tells you: *"今日洞见已凝结完毕"* — and goes quiet.

---

## How It Works

Raw content from your subscriptions enters a 4-node LangGraph pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph DAG                            │
│                                                             │
│   RSS / News API                                            │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────┐    ┌───────────┐    ┌────────┐    ┌────────┐ │
│   │  Scout  │───▶│ Distiller │───▶│ Critic │───▶│ Editor │ │
│   └─────────┘    └───────────┘    └────────┘    └────────┘ │
│   broad search   strip noise      red-team       vector     │
│   across feeds   extract facts    review +       match +    │
│                  logic chains     retry if weak  store      │
│                                        │                    │
│                                   (retry ≤3)                │
│                                        │                    │
│                                        ▼                    │
│                              5–10 insight cards / day       │
└─────────────────────────────────────────────────────────────┘
```

**CriticNode** is the quality gate: if an insight lacks sufficient evidence, it routes back upstream and demands more. Hard retry limit of 3 prevents runaway token spend.

**MemoryEditorNode** vector-searches your full history of past insights. If today's finding contradicts or extends something from six months ago, it surfaces that connection — *historical insight* — as part of the card.

---

## Tech Stack

### Backend

| Layer | Technology | Why |
|---|---|---|
| Agent orchestration | **LangGraph** StateGraph + DAG | Strict state machine, no runaway loops, visual debugging via LangGraph Studio |
| Structured LLM output | **Instructor + Pydantic V2** | Forces LLM into strongly-typed models; built-in retry on schema mismatch. Target: ≥99% success rate over 100 consecutive calls |
| Vector memory | **ChromaDB + BAAI/bge-m3** | Local deployment, multilingual embeddings; Repository Pattern ready for Qdrant migration |
| API | **FastAPI** async | Native asyncio for concurrent LLM I/O and crawler requests |
| Task queue | **Celery + Redis** | Nightly deep-distillation jobs run async; Redis also backs distributed locks |
| Database | **PostgreSQL + SQLAlchemy 2.0 async + Alembic** | Strong transactions for card/config persistence |
| Cost control | Token monitor + daily budget cap | $50/day hard limit during development; $1.5k–3k/month at scale |

### Android Client

| Layer | Technology |
|---|---|
| UI | **Kotlin + Jetpack Compose** — declarative, zero XML |
| Architecture | **MVI** (Model-View-Intent) + Unidirectional Data Flow |
| State | `StateFlow` + `collectAsStateWithLifecycle()` |
| DI | **Dagger Hilt** |
| Persistence | **Room** (offline-first) |
| Networking | **Retrofit2** |

---

## Design Principles

**Anti-infinite-scroll.** Fixed daily output. The "All Caught Up" terminal state is a first-class feature, not an afterthought — no load-more button, no suggestions, just a single line that fades in: *今日洞见已凝结完毕.*

**Zero hallucination tolerance.** LangGraph's state machine enforces explicit transitions. Instructor + Pydantic V2 locks LLM output into strongly-typed contracts. Non-determinism is confined to the smallest possible content-generation sandbox.

**Compute for cognition.** The system does the heavy reading so you don't have to. Every card must have a verifiable logic chain (`LogicPoint[]`) and at least two independent sources before it leaves the pipeline.

---

## Key Data Model

```python
class FinalBriefing(BaseModel):
    category: str          # e.g. "AI Engineering"
    core_thesis: str       # ≤40 chars, no adjective stacking
    logic_chain: List[LogicPoint]   # 2–5 nodes, premise → conclusion
    historical_insight: Optional[str]  # cross-time contradiction / extension
    sources: List[Source]  # each URL-validated
    confidence_score: float  # CriticNode output; <0.7 → marked unverified
```

---

## Project Structure

```
insight/
├── backend/
│   ├── app/
│   │   ├── services/agents/     # Scout, Distiller, Critic, Editor
│   │   ├── services/llm/        # Instructor client + cost tracker
│   │   ├── services/vector/     # ChromaDB Repository (swap-ready)
│   │   ├── models/llm/          # Pydantic contracts (FinalBriefing, etc.)
│   │   └── api/v1/              # FastAPI endpoints
│   └── tests/                   # unit + integration, phase-gated
├── android/
│   └── app/src/main/java/com/insight/app/
│       ├── feature/insight/     # InsightState / Intent / Effect (MVI)
│       ├── core/data/           # Room + Retrofit repositories
│       └── core/di/             # Hilt modules
└── 技术文档.md                   # 8,000+ word technical specification
```

---

## Documentation

The full technical spec lives at [`技术文档.md`](./技术文档.md) — 8,000+ words covering:

- Product philosophy and competitive analysis (Feedly / Inoreader / Readwise / AlphaSense)
- Tech selection rationale: **LangGraph vs CrewAI**, **ChromaDB vs Qdrant vs Milvus** (with benchmark tables)
- LangGraph state schema and node definitions
- Android MVI state machine contract (sealed interfaces)
- Risk assessment: token cost runaway, anti-scraping compliance, hallucination mitigation
- Cost budget: $1.5k–3k/month at 10 topics/day

This document was written *before* any code as the collaboration contract with the AI development assistant. The code is generated from it.

---

## Getting Started

```bash
# Clone
git clone https://github.com/Zongq1/Insight.git
cd Insight/backend

# Install dependencies
pip install poetry && poetry install

# Configure
cp .env.example .env
# Fill in: OPENAI_API_KEY, DATABASE_URL, NEWS_API_KEY

# Start services (PostgreSQL + Redis via Docker)
docker run -d --name insight-postgres -e POSTGRES_USER=insight \
  -e POSTGRES_PASSWORD=insight123 -e POSTGRES_DB=insight \
  -p 5432:5432 postgres:16-alpine

docker run -d --name insight-redis -p 6379:6379 redis:7-alpine

# Migrate and run
alembic upgrade head
uvicorn app.main:app --reload
# API docs → http://localhost:8000/docs
```

---

<div align="center">

Built entirely with **[Claude Code](https://claude.ai/code)** — from architecture design and schema definition to code generation and debugging.

</div>
