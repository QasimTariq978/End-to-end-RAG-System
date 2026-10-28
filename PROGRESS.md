# Progress

Track your progress through the masterclass. Update this file as you complete modules - Claude Code reads this to understand where you are in the project.

## Convention
- `[ ]` = Not started
- `[-]` = In progress
- `[x]` = Completed

## Modules

### Module 1: App Shell + Observability

Plan: `.agent/plans/1.app-shell.md`. Code is written for every task. Items marked `[-]` still need their live validation, which requires `backend/.env` and `frontend/.env`.

- [x] A1 Root `.gitignore`
- [x] A2 Database schema + RLS (`001` and `002_grants.sql` applied; newer Supabase projects need explicit grants to `authenticated`)
- [x] A3 Backend scaffold + venv (health test passes)
- [x] A4 Frontend scaffold (build + lint pass)
- [x] B1 Auth dependency (no header and garbage token both 401 against live Supabase)
- [x] B2 Threads + messages endpoints (live: create, list, messages, auto-title)
- [x] B3 LLM service with LangSmith tracing. OpenRouter free models with stateless completions and history from Supabase (plan `.agent/plans/2.openrouter-switch.md`). Live: multi-turn memory works; traces land in LangSmith with status success.
- [x] B4 SSE chat endpoint (live: `delta` events stream, then `done`; assistant message saved)
- [x] C1 Auth UI (sign up / sign in confirmed in browser)
- [x] C2 API client + SSE parser (type-checks)
- [x] C3 Chat UI (streaming chat confirmed in browser)
- [x] C4 RLS isolation check (live via API: user B sees 0 threads and gets 404 on read, delete and post to A's thread; A's thread survives)
- [x] D1 Docs + progress (README "Running Locally" added, with the grants migration and frontend env notes)

### Module 2: BYO Retrieval + Memory

Split into two sub-plans. Embeddings: `openai/text-embedding-3-small` via OpenRouter (1536 dims). Needs OpenRouter credit.

**Plan 3: Ingestion** (`.agent/plans/3.ingestion.md`)
- [ ] A1 Migration `003_documents.sql` (pgvector, documents/chunks, Storage bucket, Realtime)
- [ ] B1 Config + deps
- [ ] B2 Chunking service
- [ ] B3 Embeddings service
- [ ] B4 Ingestion service
- [ ] B5 Documents router
- [ ] B6 Live backend check
- [ ] C1 API client
- [ ] C2 `useDocuments` + Realtime
- [ ] C3 Documents page + nav
- [ ] C4 Browser check
- [ ] D1 Docs + progress

**Plan 4: Retrieval tool** (`.agent/plans/4.retrieval-tool.md`)
- [ ] A1 Migration `004_match_chunks.sql`
- [ ] B1 Config
- [ ] B2 Retrieval service
- [ ] B3 Tool loop in `llm.py`
- [ ] B4 Executor unit test
- [ ] B5 Live check + threshold tuning
- [ ] C1 API types
- [ ] C2 Chat state + rendering
- [ ] C3 Browser check
- [ ] D1 Docs, progress, push
