## 1. Unified Pipeline Infrastructure

- [x] 1.1 Create `src/data_pipeline/full_ingest_neo4j.py` skeleton with Neo4j driver connection.
- [x] 1.2 Implement the main document loop over `metadata_deduped.parquet`, applying the filter for `loai_van_ban` in `['Thông tư', 'Nghị định', 'Luật', 'Bộ luật']` and `ngay_ban_hanh` >= '2000-01-01'.
- [x] 1.3 Implement Stage 1 (Shell Ingestion): create/merge Document nodes using Cypher with metadata properties.

## 2. Core Processing Stages

- [x] 2.1 Implement Stage 2 (Preamble Extraction): Parse the text before "Điều 1" to extract context variables, specifically identifying the Primary Target document for modifications.
- [x] 2.2 Implement Stage 3 (Segmentation): Integrate the HTML parser to split the document body and ingest Chapters, Articles, Clauses, and Points into Neo4j.
- [x] 2.3 Implement Stage 4 (Cross-Reference Extraction): Dynamically extract internal references and external references (via lookup).
- [x] 2.4 Implement Context-Aware Modification Extraction: Use the Primary Target from Stage 2 to accurately create `MODIFIES` relationships for implicit references like "sửa đổi Điều X".

## 3. Optimization and Execution

- [x] 3.1 Implement transaction batching logic to periodically commit to Neo4j, preventing memory overload.
- [x] 3.2 Add robust error handling to log and skip problematic documents without halting the pipeline.
- [x] 3.3 Execute the unified pipeline on the full dataset and verify the resulting graph topology in Neo4j.
