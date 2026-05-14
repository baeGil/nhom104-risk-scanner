## Context

The current data ingestion process for the Vietnamese Legal Knowledge Graph is fragmented. The separation of metadata ingestion, segmentation parsing, and cross-reference extraction has led to a loss of critical context. Specifically, modification references often refer implicitly to a "target document" declared in the preamble (căn cứ). Without passing this preamble context to the extraction phase, relationships are inaccurate or dropped. Furthermore, relying on static files like `relation.parquet` causes orphaned relationships if document shells are missing.

## Goals / Non-Goals

**Goals:**
- Implement a 4-stage unified pipeline per document: Shell Ingestion -> Preamble Context Scan -> Hierarchical Segmentation -> Context-Aware XRef Extraction.
- Propagate preamble context (Primary Target) to resolve ambiguous modification references (e.g., "sửa đổi, bổ sung Điều 3").
- Directly ingest extracted relationships and segments into Neo4j within the same script.
- Filter ingestion to only include `Thông tư`, `Nghị định`, `Luật`, `Bộ luật` from year 2000 onwards.

**Non-Goals:**
- Rewriting the core Regex patterns for extraction (we reuse existing logic).
- Implementing the "Composite View" (Effective Text) generation; this will remain a separate downstream phase.

## Decisions

- **Single Orchestrator:** We will use `src/data_pipeline/full_ingest_neo4j.py` as the main entry point to orchestrate all 4 stages per document, rather than batching each stage for the entire corpus. This ensures memory efficiency and context locality.
- **Preamble Context Passing:** The preamble is scanned before segmentation. Extracted context variables (like the primary target document) are kept in memory and passed directly to the extraction functions when processing the document's segments.
- **Dropping relation.parquet:** We will deprecate the static `relation.parquet` in favor of dynamic extraction to ensure graph integrity (relationships are only created when both endpoints exist or can be deterministically stubbed).

## Risks / Trade-offs

- **Risk:** High memory usage and Neo4j transaction timeouts due to processing 178k documents in one go.
  **Mitigation:** Implement batching (e.g., commit every 100 documents) and flush Neo4j sessions periodically. Ensure Neo4j heap size is adequately configured (already done in `.env`).
- **Risk:** Parser errors breaking the pipeline loop.
  **Mitigation:** Add robust `try...except` blocks around the segmentation and extraction logic for each document so that a single failure does not halt the entire pipeline.
