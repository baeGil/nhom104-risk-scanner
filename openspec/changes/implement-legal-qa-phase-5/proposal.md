## Why

Phase 5 needs a clear implementation plan for the legal QA pipeline after T5.1 intent analysis is already in place. The project now has a stronger Phase 4 legal retrieval core, so QA should reuse that retrieval surface instead of building a separate Article-only path.

## What Changes

- Implement the Phase 5 legal QA pipeline for pure legal questions first.
- Route intent analysis output into normalized QA sub-queries and retrieval plans.
- Reuse the Phase 4 `LegalHybridRetriever`/matching core for topic and scenario-style QA retrieval.
- Keep direct lookup for specific legal references such as `Điều X`, `khoản Y`, and `điểm Z`.
- Generate strict JSON answers for backend consumption, including answer text, citations, retrieved provisions, intent metadata, and validity notes.
- Apply citation verification to QA answers using graph UIDs first, with citation text parsing as fallback.
- Treat validity as best-effort because current relationship and effective-text data may be incomplete.
- Defer complex comparison workflows, streaming delivery, frontend work, and authoritative effective-text composition.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `question-intent-analysis`: Define the QA-first mapping from intent output to normalized sub-query plans.
- `retrieval-pipeline`: Rework Phase 5 retrieval around Phase 4 hybrid legal segment retrieval, direct lookup, and best-effort validity signals.
- `answer-generation`: Require strict backend-oriented JSON output for QA answers and citations.
- `citation-verification`: Apply UID-first verification to QA citations and expose verification status in the QA response.

## Impact

- Affected modules: `src/llm/intent.py`, `src/llm/models.py`, `src/llm/retriever.py`, `src/llm/prompts.py`, `src/llm/citation_verifier.py`.
- Reused modules: `src/contract/hybrid_retriever.py`, `src/contract/matcher.py`, `src/contract/query_rewriter.py`, `src/contract/citations.py`.
- New likely modules: a QA orchestration service and answer generation service under `src/llm/`.
- No new external dependency is expected.
- Validity output will be explicit about uncertainty until `MODIFIES`, `SUPERSEDES`, and `EffectiveArticle` coverage improves.
