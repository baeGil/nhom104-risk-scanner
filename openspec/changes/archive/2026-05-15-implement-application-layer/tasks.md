# Implement Application Layer — Tasks

## 1. Bug Fixes & Infrastructure

- [x] 1.1 Fix prompt template syntax in `src/llm/prompts.py` — change `{var}` to `{{var}}` for clause_extraction, compliance_analysis, and answer_generation templates
- [x] 1.2 Create `pytest.ini` with test configuration (testpaths, markers, asyncio_mode)
- [x] 1.3 Create root `conftest.py` with shared fixtures (mock LLM, mock Neo4j, sample contracts, PII test texts)
- [x] 1.4 Build `MockLLMProvider` in `src/llm/mock_provider.py` implementing LLMClient interface with predefined responses for intent_analysis, clause_extraction, compliance_analysis, answer_generation
- [x] 1.5 Update `src/config.py` to support `LLM_PROVIDER=mock` configuration
- [x] 1.6 Create `src/contract/mock_bridge.py` with MockEmbeddingService, MockGraphTraversal, MockEffectiveTextService — config-driven switching via src/config.py
- [x] 1.7 Create sample contract mock data in `data/sample_contracts/` — sample_hop_dong_thue.md, sample_hop_dong_lao_dong.md, sample_hop_dong_mua_ban.md with known clauses for testing

## 2. Contract Review Pipeline (HIGH PRIORITY — Demo Focus)

- [x] 2.1 Add `ContractClause` dataclass and `ClauseType` enum to `src/contract/models.py`
- [x] 2.2 Create `src/contract/clause_extractor.py` with `ClauseExtractor` class — LLM-based extraction from Contract.redacted_text
- [x] 2.3 Integrate embedding generation for extracted clauses using vietlegal-harrier-0.6b (1024-dim)
- [x] 2.4 Add `ComplianceResult`, `ComplianceViolation`, `RiskLevel` dataclasses to `src/contract/models.py`
- [x] 2.5 Create `src/contract/matcher.py` with `LegalMatcher` class — vector search + fulltext fallback + graph traversal + reranking
- [x] 2.6 Implement hybrid search: combine vector similarity (article_embeddings) + fulltext (article_fulltext) results
- [x] 2.7 Implement authority-weighted reranking: combined_score = semantic × authority (Luật 3.0, ND 2.0, TT 1.5) × graph_boost (1.5×)
- [x] 2.8 Create `src/contract/compliance_analyzer.py` with `ComplianceAnalyzer` class — LLM prompt with clause + provisions + effective text + amendment history
- [x] 2.9 Create `src/llm/citation_verifier.py` with `CitationVerifier` class — parse Vietnamese legal citations, verify against Neo4j
- [x] 2.10 Add `PolicyClassification` dataclass and create `src/contract/policy_review.py` — compliant_and_efficient, compliant_but_restrictive, non_compliant
- [x] 2.11 Write tests for all contract review components with sample contracts

## 3. Retrieval Engine (T5.2)

- [x] 3.1 Add `RetrievedProvision`, `RetrievalResult` dataclasses to `src/llm/models.py`
- [x] 3.2 Create `src/llm/retriever.py` with `RetrievalEngine` class and `RetrievalStrategy` ABC — routes by SubQuery.retrieval_strategy
- [x] 3.3 Implement `DirectLookupStrategy` — resolve so_ky_hieu → doc_id, MATCH Article by uid
- [x] 3.4 Implement `VectorSearchStrategy` — embed query, call db.index.vector.queryNodes, filter by is_current + loai_van_ban
- [x] 3.5 Implement `GraphTraversalStrategy` — traverse REFERENCES_INTERNAL, REFERENCES_EXTERNAL, MODIFIES, DETAILS
- [x] 3.6 Implement `HybridSearchStrategy` — combine fulltext + vector results with deduplication
- [x] 3.7 Implement `ValidityCheckStrategy` — check is_current, SUPERSEDED_BY relationships
- [x] 3.8 Implement `ComparisonStrategy` — parallel lookups, return side-by-side with diff
- [x] 3.9 Create `src/llm/reranker.py` — combined scoring, return top-5 per query
- [x] 3.10 Write tests for RetrievalEngine with mock Neo4j

## 4. QA Pipeline (T5.3 / T5.4)

- [x] 4.1 Add `AnswerResult` dataclass to `src/llm/models.py`
- [x] 4.2 Create `src/llm/answer_generator.py` with `AnswerGenerator` class — prompt assembly + LLM call + JSON parsing
- [x] 4.3 Write tests for AnswerGenerator with mock provisions
- [x] 4.4 Reuse CitationVerifier (T4.5) for QA citation verification (T5.4) — no new code needed, just integration

## 5. Embedding Service Deployment

- [x] 5.1 Verify `infra/embedding_service/app.py` is functional — check model loading, /embed endpoint, /health endpoint
- [x] 5.2 Fix port inconsistency — align config.py (8001), Dockerfile (8080), app.py __main__ (8080) to single port
- [x] 5.3 Deploy embedding service — docker-compose up or direct uvicorn, verify /health returns status=ok
- [x] 5.4 Run `ArticleEmbedder.embed_all()` on ingested data — batch 512 articles per API call, verify embeddings stored
- [x] 5.5 Verify vector index `article_embeddings` is ONLINE in Neo4j — test with sample query vector

## 6. FastAPI Backend

- [x] 6.1 Create `infra/api/` directory structure with `__init__.py`
- [x] 6.2 Create `infra/api/app.py` with FastAPI app, CORS middleware (allow localhost:3000), health check endpoint
- [x] 6.3 Create `infra/api/models.py` with Pydantic schemas: ChatRequest, ChatChunk, ConversationSummary, JobStatusResponse, UploadResponse
- [x] 6.4 Create `infra/api/sse.py` with SSE streaming utilities — format_sse, event_stream generator
- [x] 6.5 Create `infra/api/job_store.py` — in-memory job store for async contract review (job_id → status, progress, results)
- [x] 6.6 Create `infra/api/contract_routes.py` — POST /api/contracts/upload (async job), GET /api/contracts/{jobId}/status (polling), GET /api/contracts/history
- [x] 6.7 Create `infra/api/qa_routes.py` — POST /api/qa/chat (SSE streaming), POST/GET/DELETE /api/qa/conversations (in-memory via ConversationManager)
- [x] 6.8 Create `infra/api/middleware.py` — error handling, structured logging, request timing
- [x] 6.9 Add requirements to `requirements.txt` — fastapi, uvicorn, python-multipart
- [x] 6.10 Write tests for all API endpoints

## 7. Frontend Integration

- [x] 7.1 Fix `frontend/src/app/(app)/contract-review/page.tsx` — call uploadContract(), poll getJobStatus(), display results from real API
- [x] 7.2 Fix `frontend/src/app/(app)/legal-qa/page.tsx` — import from `@/lib/api` switcher instead of direct mock import
- [x] 7.3 Fix `frontend/src/lib/api-contract.ts` — use `apiRequest()` instead of raw fetch for uploadContract() (adds auth, retry, timeout)
- [x] 7.4 Set `NEXT_PUBLIC_USE_MOCK_API=false` in `.env.local` to activate real API
- [x] 7.5 Test end-to-end: Contract upload → job polling → clause cards → compliance report → verified citations
- [x] 7.6 Test end-to-end: QA chat → SSE streaming → provision cards → citation badges

## 8. Polish & Demo Prep

- [x] 8.1 Add structured logging to all pipeline components (contract review, QA, retrieval)
- [x] 8.2 Add retry logic with exponential backoff for LLM calls and embedding service calls
- [x] 8.3 Add timeout handling for Neo4j queries (30s default)
- [x] 8.4 Add error boundaries and user-friendly error messages in FastAPI
- [x] 8.5 Run full test suite, fix any failures
- [x] 8.6 Prepare demo scripts — sample contract upload + sample QA questions with expected outputs
