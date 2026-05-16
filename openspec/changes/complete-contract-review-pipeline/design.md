## Context

The original Task 4 plan assumed Article-level retrieval over an `article_embeddings` vector index, followed by graph traversal and EffectiveArticle-based compliance analysis. The current graph has evolved differently: embeddings are loaded mostly on Clause and Point nodes, references from the LLM are stored as a single `REFERENCES` relationship with raw type metadata, and T3 effective-text composition is intentionally deferred.

The existing code already contains partial modules for contract parsing, clause extraction, matching, compliance analysis, citation verification, and policy review. The production API still returns mock contract review results, and the current matcher does not fit the live graph because it searches Article nodes and treats full-text search as fallback instead of running true hybrid retrieval.

## Goals / Non-Goals

**Goals:**

- Deliver a real contract review pipeline across backend/library, API, and frontend.
- Use LLM query rewrite before retrieval so contract clauses become legal search plans rather than raw semantic queries.
- Perform hybrid retrieval across Article, Clause, and Point legal segments.
- Return complete legal context from Document title down to Article, Clause, and Point when available.
- Use `REFERENCES` and `MODIFIES` graph signals to improve context and flag validity risks.
- Verify citations deterministically using graph UIDs while still rendering human-readable legal citations.
- Persist jobs and review outputs durably for history and frontend result pages.
- Add tests and eval fixtures that measure retrieval, citation verification, and end-to-end behavior.

**Non-Goals:**

- Compose full EffectiveArticle text or complete the deferred T3.x effective-text pipeline.
- Reintroduce document-level T1.7 relationships as a primary retrieval dependency.
- Guarantee legal advice quality beyond retrieval-backed compliance analysis and citation verification.
- Store user-uploaded contracts inside the Neo4j legal graph.

## Decisions

### Use LegalSegment retrieval instead of Article-only retrieval

Article-only search is no longer aligned with the data. The graph currently has embeddings on Article, Clause, and Point nodes, with most embeddings on Clause and Point. The implementation will add an indexable retrieval surface across all three levels, preferably by applying a shared `LegalSegment` label to embedded Article, Clause, and Point nodes.

Alternative considered: keep the existing `article_embeddings` design and roll Clause/Point text up into Article embeddings. This loses precision for point-level matching and wastes the already-generated leaf embeddings.

### Use true hybrid search, not vector search with fallback

Hybrid retrieval will run multiple candidate generators and merge by `uid`:

- Vector search over embedded legal segments.
- Full-text search over legal segment text and titles.
- Exact or boosted matches for rewritten keywords, legal terms, title hints, and citation-like text.
- Graph expansion over `REFERENCES` and `MODIFIES`.

Fallback-only full-text search is insufficient because legal clauses often require both semantic similarity and exact legal phrase matching.

### Add LLM query rewrite before retrieval

Contract text is not an ideal legal search query. A query rewrite step will turn each extracted contract clause into a structured retrieval plan containing legal issue, rewritten queries, keywords, expected law domains or titles, risk type, and optional filters. The retriever will search using both the raw clause and rewritten fields.

Alternative considered: search directly with clause text. This is simpler but underperforms for legal issues such as penalty caps, unilateral termination, wage obligations, confidentiality, and dispute resolution where the relevant law uses different wording.

### Keep a single REFERENCES relationship with type properties

The graph will keep `REFERENCES` as the traversal relationship and store the original reference category as `ref_type` or `raw_type` (`internal`, `external`). This avoids splitting queries into multiple edge types while preserving semantic detail.

Alternative considered: migrate to `REFERENCES_INTERNAL` and `REFERENCES_EXTERNAL`. This is clearer at the schema level but adds migration complexity and does not materially improve Task 4 retrieval.

### Use MODIFIES as a validity signal, not full effective-text composition

When a matched provision has related `MODIFIES` edges, the pipeline will surface a validity warning and include modification context for the LLM. It will not attempt to merge amendment text into a final effective provision in this change.

This supports practical review now while leaving T3.x effective-text composition for a later change.

### Verify citations by UID and display text

Compliance output will carry both a display citation and a stable graph UID. Verification will resolve the UID against Neo4j, check the node exists, and compare basic metadata such as article/clause/point path and document title when available. The displayed citation remains user-friendly, but correctness is anchored to graph identity.

Parsing citation text alone is fragile because Vietnamese legal citations may omit document numbers, use short titles, or vary wording.

### Persist contract review data outside Neo4j

Contract jobs, extracted clauses, matches, compliance outputs, and citation verification records should be stored in application storage, preferably Supabase/Postgres. Neo4j remains the legal knowledge graph. This keeps user data separate from source legal data and supports permissions, history, deletion, and retry workflows.

## Risks / Trade-offs

- LLM rewrite can produce poor search plans → keep raw clause text as a retrieval input, log rewrite output, and add retrieval regression tests.
- Vector index setup may drift from live labels/properties → add startup/index validation and a migration task that labels embedded nodes consistently.
- MODIFIES context is incomplete without T3.x → clearly mark validity as a signal (`possibly_modified`, `current_unknown`, `latest_known`) rather than definitive effective text.
- GPT-4o-mini OCR can be costly and slow → use direct text extraction for TXT/MD and text-layer PDFs before vision OCR; batch pages and set file-size/page limits.
- Citation verification by UID requires compliance analysis to preserve matched node IDs → enforce structured LLM output with citation objects that include `uid`.
- Durable persistence adds schema and migration work → isolate persistence behind a repository interface so local development can use an in-memory or file-backed implementation.

## Migration Plan

1. Add graph migration scripts for `LegalSegment` labeling and vector/full-text indexes.
2. Implement the new retrieval pipeline behind a new service interface while keeping existing matcher code available for comparison.
3. Wire the contract API to the real pipeline behind a configuration flag.
4. Add persistence tables/repositories and migrate job status/history from in-memory storage.
5. Enable frontend rendering of real clauses, matches, citations, and compliance results.
6. Run golden contract and retrieval regression tests before removing mock-only behavior.

Rollback strategy: keep the existing mock job path behind a development-only flag until the real pipeline passes smoke tests. If retrieval or LLM calls fail in production, jobs should fail with explicit error state rather than returning fabricated compliance.

## Open Questions

- Which application store should be the first durable backend: Supabase tables already used by the frontend, or a backend-local SQLite/Postgres setup for faster iteration?
- Should GPT-4o-mini OCR use the OpenAI Responses API directly, or be wrapped through the existing LLM client abstraction?
- What is the initial golden contract set for retrieval/compliance evaluation?
