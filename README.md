# Sightline

**Multimodal Agentic Equity-Research Analyst** — ask a question about a public
company and get a cited, fact-checked brief grounded in SEC filings and
earnings calls.

The differentiator: retrieval runs over **page images** (not pre-chunked text),
so tables and charts survive, and a **critic loop** verifies every numeric claim
against extracted figures before the brief is written.

## Stack

OpenAI (reasoning) · local HF models on Apple M5 Pro (MPS / MLX) · LangGraph ·
pgvector · FastAPI

## Status

🚧 Phase 0 — Foundations. See the build roadmap for the full plan.
