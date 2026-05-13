## Context

Neo4j is running (neo4j:5.15-community on localhost:7687) but empty. All data files are present:
- `data/metadata_deduped.parquet` — 21K deduplicated documents (2.2MB)
- `data/relationships.parquet` — 659K document relationships (433KB)
- `output/neo4j_schema.cypher` — schema with constraints and indexes (already generated)

The data pipeline (T0.1–T0.5, T1.7) has completed. Người B's segmentation code (T1.1–T1.6) and Người C's app layer (T4.1, T5.1) are ready but blocked by empty graph.

## Goals / Non-Goals

**Goals:**
- Ingest all Document nodes (~21K) and relationships (~659K) into Neo4j
- Fix vector index dimension from 768 → 1024 to match harrier-0.6b model
- Create idempotent ingest scripts that can be re-run safely
- Verify data integrity after ingestion

**Non-Goals:**
- Does NOT ingest Article/Clause/Point nodes (that's Người B's T1.5)
- Does NOT generate embeddings (that's Người B's T1.6)
- Does NOT create EffectiveArticle nodes (that's Người B's T3.3)
- Does NOT extract cross-references (that's Người B's T2.x)

## Decisions

### D1: Use scratch_ingest_nodes.py for Document nodes (not rewrite)

**Decision**: Use Người A's existing `scratch_ingest_nodes.py` script with minor fixes.

**Rationale**: The script already reads `metadata_deduped.parquet`, batches at 5K, and uses MERGE. Rewriting adds no value.

**Fixes needed**:
- Typo: `ngay_ban_anh` → `ngay_ban_hanh` in Cypher SET clause
- Add more metadata fields: `tinh_trang_hieu_luc`, `co_quan_ban_hanh`, `nganh`, `linh_vuc`

**Alternatives considered**:
- Rewrite as proper module in `src/data_pipeline/`: Rejected — overkill for one-time ingest
- Use `neo4j-admin import` (bulk CSV): Rejected — requires CSV export, more complex setup

### D2: Use neo4j_ingest.py for relationships (not rewrite)

**Decision**: Use existing `src/data_pipeline/neo4j_ingest.py` as-is.

**Rationale**: Already handles 16 relationship types, batch MERGE, orphan validation, and logging. The recent commit added 5 more types (CAN_CU, SUA_DOI, etc.) and fixed f-string escaping.

### D3: Fix schema file directly (not regenerate)

**Decision**: Edit `output/neo4j_schema.cypher` to change `vector.dimensions` from 768 to 1024.

**Rationale**: The schema file is already generated and correct except for this one value. Regenerating requires writing a schema generator (T1.4 proper), which is out of scope.

**Alternatives considered**:
- Write schema generator: Deferred — not needed for this change
- Override via Neo4j config: Not possible — vector index dimensions are set at creation time

### D4: Run schema via cypher-shell (not Python driver)

**Decision**: Use `cypher-shell -f output/neo4j_schema.cypher` to apply schema.

**Rationale**: Schema file contains 20+ Cypher statements including constraints and vector indexes. cypher-shell handles multi-statement files natively. Python driver would require parsing and executing each statement individually.

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Neo4j OOM with 21K nodes + 659K edges | High | Heap is 2G, page cache 1G — sufficient for this scale. Monitor with `docker stats`. |
| Duplicate Document IDs from bad dedup | Medium | MERGE handles duplicates. Verify count matches metadata_deduped.parquet row count. |
| Relationship orphan nodes (missing endpoints) | Low | neo4j_ingest.py validates endpoints and logs orphans. Skips invalid relationships. |
| Vector index dimension mismatch breaks T1.6 | High | Fixed in this change. Verify with `SHOW INDEXES` after schema apply. |
| Password mismatch between .env and Neo4j | Medium | Verified: .env has `team104vinuni`, docker-compose uses same value. |
