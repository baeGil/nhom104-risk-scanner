## 1. Fix Schema File

- [x] 1.1 Update `output/neo4j_schema.cypher` vector index dimension from 768 to 1024
- [x] 1.2 Apply schema to Neo4j via `cypher-shell -f output/neo4j_schema.cypher`
- [x] 1.3 Verify schema: run `SHOW CONSTRAINTS` and `SHOW INDEXES` to confirm all constraints and indexes exist

## 2. Fix and Run Document Node Ingestion

- [x] 2.1 Fix typo in `scratch_ingest_nodes.py`: change `ngay_ban_anh` to `ngay_ban_hanh`
- [x] 2.2 Add missing metadata fields to ingest script: `tinh_trang_hieu_luc`, `co_quan_ban_hanh`, `nganh`, `linh_vuc`
- [x] 2.3 Run ingest script to load ~21K Document nodes into Neo4j
- [x] 2.4 Verify: `MATCH (d:Document) RETURN count(d)` returns expected count matching metadata_deduped.parquet rows

## 3. Run Relationship Ingestion

- [x] 3.1 Run `src/data_pipeline/neo4j_ingest.py` to ingest relationships from `data/relationships.parquet`
- [x] 3.2 Verify: check orphan count in `output/orphan_relationships.json`
- [x] 3.3 Verify: `MATCH ()-[r]->() RETURN count(r)` returns expected count

## 4. Final Validation

- [x] 4.1 Run validation query: compare Neo4j Document count vs metadata_deduped.parquet row count
- [x] 4.2 Run validation query: compare Neo4j relationship count vs valid relationships in parquet
- [x] 4.3 Verify vector index: `SHOW INDEXES` confirms `article_embeddings` has 1024 dimensions
- [x] 4.4 Test sample query: lookup a Document by so_ky_hieu and verify its relationships
