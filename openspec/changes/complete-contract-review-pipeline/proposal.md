## Why

The current contract review code has useful pieces for parsing, clause extraction, matching, compliance analysis, citation verification, and policy review, but the production API still returns mock results and the matcher no longer matches the current graph shape. The legal graph now has embeddings primarily on Clause and Point nodes, LLM-extracted references, and a need for query rewrite plus hybrid retrieval rather than Article-only vector search.

## What Changes

- Replace the mock contract processing path with a real end-to-end pipeline: OCR/text parsing, LLM clause extraction, query rewrite, hybrid legal retrieval, graph-aware context expansion, compliance analysis, citation verification, persistence, and frontend display.
- Change legal matching from Article-only vector search to LegalSegment retrieval across Article, Clause, and Point nodes.
- Add query rewrite before retrieval so contract clauses become legal search plans with legal issue, rewritten queries, keywords, expected domains, and risk type.
- Implement hybrid search that combines vector search, lexical/full-text search, exact title/citation signals, reference expansion, MODIFIES validity signals, and reranking.
- Keep references as a single `REFERENCES` relationship while preserving `ref_type`/`raw_type` properties for internal and external references.
- Use `MODIFIES` relationships to flag provisions that may be amended, replaced, supplemented, or no longer current without requiring full effective-text composition in this change.
- Add GPT-4o-mini-based OCR for scanned PDFs/images, with cheaper direct text extraction for TXT/MD and text-layer PDFs where possible.
- Verify citations using a hybrid method: human-readable citation text for display, stable graph `uid` for deterministic verification.
- Persist contract jobs, extracted clauses, matches, compliance results, and citation verification results in application storage rather than Neo4j legal graph nodes.
- Add production-style tests and evaluation fixtures for parsing, retrieval, citation verification, API processing, and frontend result display.

## Capabilities

### New Capabilities

- `legal-hybrid-retrieval`: Query rewrite and hybrid retrieval over Article, Clause, and Point legal segments with graph-aware reranking.

### Modified Capabilities

- `contract-review-pipeline`: Replace Article-only matching assumptions with query rewrite, hybrid search, LegalSegment context assembly, MODIFIES validity checks, real citation verification, and production persistence.
- `backend-api`: Contract upload/status/history endpoints shall run and expose the real pipeline instead of mock job results.
- `contract-review-ui`: Contract review UI shall render real clauses, matched legal provisions, verified citations, and persisted job history from the backend.
- `test-infrastructure`: Add golden-contract, retrieval, citation verification, API smoke, and regression evaluation coverage for the production contract review flow.

## Impact

- Affected backend modules: `src/contract/*`, `src/llm/citation_verifier.py`, `src/embeddings/retriever.py`, `infra/api/contract_routes.py`, `infra/api/models.py`, and job persistence code.
- Affected frontend modules: `frontend/src/lib/api-contract.ts`, `frontend/src/app/(app)/contract-review/page.tsx`, and related result display types.
- Affected graph setup: add a `LegalSegment` label or equivalent indexable target for Article, Clause, and Point nodes with embeddings; create vector and full-text indexes for hybrid retrieval.
- Affected storage: add durable tables or equivalent persistence for contract jobs and review outputs, preferably in Supabase/Postgres; Neo4j remains the legal knowledge graph.
- External dependencies: LLM calls for query rewrite, clause extraction, compliance analysis, and GPT-4o-mini OCR; Neo4j vector/full-text indexes for retrieval.
