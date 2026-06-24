# Project Insight

> AI-powered daily briefing tool — distills thousands of words into 5–10 insight cards per day, then stops. No infinite scroll.

## What it does

Project Insight is built for information overload. It pulls content from your subscriptions, runs it through a 4-node multi-agent pipeline, and delivers a fixed number of insight cards each day. When you're done reading, it says so — and stops.

```
Raw feeds (10,000+ words)
        ↓
  Scout     → broad retrieval across sources
  Distiller → strip noise, extract logic chains
  Critic    → red-team review, retry if weak
  Editor    → vector-match history, detect contradictions
        ↓
  5–10 insight cards / day  ·  done = done
```

## Architecture

| Layer | Stack |
|---|---|
| Agent orchestration | LangGraph (DAG, conditional edges, retry) |
| Structured LLM output | Instructor + Pydantic V2 (target: ≥99% success rate) |
| Vector memory | ChromaDB + BAAI/bge-m3 |
| Backend | FastAPI + Celery + Redis + PostgreSQL |
| Android client | Kotlin + Jetpack Compose + MVI + Hilt + Room |

## Design philosophy

- **Anti-infinite-scroll** — fixed daily output, "all caught up" terminal state
- **Zero hallucination tolerance** — LangGraph state machine + Instructor strong typing, no black-box probability failures
- **Compute for cognition** — LLM does the heavy lifting so you don't have to read raw internet content

## Docs

Full technical specification (8,000+ words) including competitive analysis, tech selection rationale (LangGraph vs CrewAI, ChromaDB → Qdrant migration path), and cost budget ($1.5k–3k/month): [`技术文档.md`](./技术文档.md)

## Development

See [`backend/README.md`](./backend/README.md) for setup instructions.

Built with [Claude Code](https://claude.ai/code).
