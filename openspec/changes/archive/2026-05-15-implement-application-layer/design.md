## Context

The application layer sits between the Neo4j knowledge graph and the Next.js frontend. Currently, only T4.1 (Contract Parser using MinerU) and T5.1 (Intent Analysis using OpenAI) are implemented. The remaining 14 tasks span two pipelines:

1. **Contract Review Pipeline** (T4.2-T4.6): Parse contract → extract clauses → match legal provisions → analyze compliance → verify citations → policy review
2. **Legal QA Pipeline** (T5.2-T5.4): Intent analysis (done) → retrieval → answer generation → citation verification

The data scope has been reduced from 20,982 documents to 90 documents (plain text, no relationships, no embeddings yet). The frontend UI is complete but hardcoded to mock data, bypassing the API switcher. The Neo4j database is stopped and needs rebuilding with new data.

Key constraints:
- Deadline approaching — must implement in parallel with data ingestion
- No embeddings available yet — need fulltext search fallback
- No cross-reference relationships in new data — graph traversal must be mockable
- OpenAI API required for LLM calls — no offline mock provider exists
- 3 of 4 prompt templates have broken syntax (`{var}` instead of `{{var}}`)

## Goals / Non-Goals

**Goals:**
- Implement all 14 application layer tasks with full quality — no shortcuts
- Enable parallel development using mock bridges for unavailable dependencies
- Build a complete FastAPI backend connecting frontend to Python pipeline
- Fix existing bugs (prompt templates, frontend API bypass, no mock LLM)
- Establish test infrastructure with shared fixtures and mock providers
- Design for easy swap from mock → real when data is ready

**Non-Goals:**
- Data ingestion (User B's responsibility) — but we define the interface
- Embedding service deployment (infrastructure task) — but we build the client
- Neo4j schema changes — existing schema supports all needs
- Frontend UI changes — existing components work, only API integration needed
- Cross-reference extraction (User B's responsibility) — but we build the traversal engine

## Decisions

### 1. Strategy Pattern for Retrieval Engine

**Decision**: Use Strategy pattern with `RetrievalStrategy` ABC. Each strategy (direct lookup, vector search, graph traversal, hybrid, validity check, comparison) implements `async execute(query: SubQuery) -> list[RetrievedProvision]`.

**Rationale**: Allows swapping strategies at runtime, easy to add new strategies, clean separation of concerns. The `RetrievalEngine` routes based on `SubQuery.retrieval_strategy`.

**Alternatives considered**: Single monolithic function — rejected due to complexity and testability concerns.

### 2. Fulltext Search as Primary for Demo, Vector Search as Upgrade Path

**Decision**: For the 90-document demo, use Neo4j fulltext indexes (`article_fulltext`) as the primary search mechanism. Build vector search implementation in parallel, activated when embeddings are available.

**Rationale**: 90 documents is small enough that fulltext search is sufficiently accurate. No dependency on embedding service for demo. Vector search implementation is built but not activated by default.

**Alternatives considered**: Skip fulltext, only build vector search — rejected because it blocks demo until embeddings are ready.

### 3. Mock Bridge Layer with Repository Pattern

**Decision**: Define abstract interfaces (`EmbeddingService`, `GraphRepository`, `EffectiveTextService`) with both mock and real implementations. Configuration via `src/config.py` controls which implementation is active.

**Rationale**: Clean separation, single-point swap (change config value), enables parallel development, no code changes needed when switching.

**Alternatives considered**: Conditional logic inline — rejected due to code duplication and testing complexity.

### 4. SSE Streaming via Fetch (Not EventSource)

**Decision**: Continue using the existing frontend pattern — fetch POST with readable stream reader, newline-delimited JSON with `data: ` prefix, terminated by `data: [DONE]`. Backend sets `Content-Type: text/event-stream` but frontend does not use native EventSource.

**Rationale**: Frontend already implements this pattern in `api-client.ts:apiSSE()`. No changes needed on frontend. Backend must match this wire format exactly.

### 5. Async Job Pattern for Contract Review

**Decision**: Contract review is async — upload returns `jobId`, client polls `/api/contracts/{jobId}/status`. Backend processes in background (thread pool for CPU-bound tasks, async for I/O).

**Rationale**: Contract parsing + clause extraction + compliance analysis takes 10-60 seconds. Blocking HTTP request would timeout. Job pattern allows progress tracking.

**Alternatives considered**: SSE streaming for contract review — rejected because the pipeline has discrete stages (parsing → analysis → report) better represented as job status steps.

### 6. Mock LLM Provider for Offline Development

**Decision**: Build `MockLLMProvider` implementing the `LLMClient` interface with predefined responses for known queries. Controlled by `LLM_PROVIDER=mock` in config.

**Rationale**: Current tests require real OpenAI API key, blocking offline development. Mock provider enables testing without API calls.

### 7. Prompt Template Syntax Fix

**Decision**: Standardize on double-brace `{{var}}` syntax for all templates. Update `clause_extraction`, `compliance_analysis`, and `answer_generation` templates.

**Rationale**: The `PromptTemplate.render()` method replaces `{{key}}` patterns. Single-brace templates are silently broken.

### 8. Test Infrastructure with conftest.py

**Decision**: Create root `conftest.py` with shared fixtures for Neo4j mock, LLM mock, sample documents, and PII test texts. Create `pytest.ini` with test configuration and markers.

**Rationale**: Current tests have no shared fixtures, use real API calls, and no test configuration. This blocks efficient test writing.

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data quality issues (so_hieu ≠ content) | High — retrieval returns wrong documents | Validate data before ingest; flag mismatches |
| Embeddings not ready by deadline | Medium — vector search unavailable | Fulltext fallback is sufficient for 90 docs |
| Cross-references not available | Medium — graph traversal returns empty | Traversal returns empty list gracefully; reranking still works |
| OpenAI API rate limiting | Medium — LLM calls fail | Implement retry with exponential backoff; mock provider fallback |
| Neo4j connection issues | High — all graph operations fail | Connection pooling, retry logic, health check endpoint |
| Frontend-backend integration bugs | High — UI breaks | Define API contracts upfront; test with curl before frontend integration |
| Prompt template fixes break existing T5.1 | Low — intent_analysis template is correct | Only fix broken templates; test T5.1 after changes |

## Migration Plan

1. **Phase 1** (Days 1-3): Fix bugs (prompt templates, mock provider), build RetrievalEngine core, build CitationVerifier, build ClauseExtractor
2. **Phase 2** (Days 4-6): Build LegalMatcher with mock bridge, build ComplianceAnalyzer, build AnswerGenerator, build PolicyReview
3. **Phase 3** (Days 7-8): Build FastAPI backend, fix frontend API integration, end-to-end testing
4. **Phase 4** (Days 9-10): Polish, error handling, demo prep

**Rollback**: Each phase is independently testable. If a phase fails, previous phases remain functional with mock data.

## Open Questions

1. **Who builds the data ingest script?** — If User B doesn't deliver, we need a fallback ingest script for 90 docs
2. **GPU availability for embedding service?** — Determines if we can run embeddings locally or need cloud GPU
3. **OpenAI API key quota?** — Determines if we need aggressive caching or mock-heavy testing
