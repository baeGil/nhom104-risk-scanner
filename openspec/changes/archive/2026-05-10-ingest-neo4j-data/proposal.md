## Why

All data pipeline tasks (T0.1–T0.5, T1.7) have been completed and produced clean data files, but Neo4j is empty — no Document nodes or relationships have been ingested. Without data in the graph, Người B cannot run segmentation (T1.5, T1.6) and Người C cannot build the application layer (T4.2–T5.4). This change ingests the processed data into Neo4j to unblock all downstream work.

## What Changes

- Run `neo4j_schema.cypher` to create constraints, indexes, fulltext indexes, and vector index (1024-dim for harrier-0.6b)
- Ingest ~21,000 Document nodes from `data/metadata_deduped.parquet`
- Ingest ~659,000 document-level relationships from `data/relationships.parquet`
- Fix vector index dimension mismatch: schema says 768 but embedder.py uses 1024
- Create an ingest script that can be re-run idempotently

## Capabilities

### New Capabilities
- `neo4j-data-ingestion`: End-to-end ingestion of Document nodes and relationships into Neo4j, including schema setup, batch processing, and validation

### Modified Capabilities
- `segmentation`: Vector index dimension corrected from 768 to 1024 to match harrier-0.6b model output

## Impact

- **Neo4j**: ~21K Document nodes + ~659K relationships created
- **Schema**: `article_embeddings` vector index dimension changed from 768 → 1024
- **Downstream**: Unblocks Người B (T1.5 writer, T1.6 embedder) and Người C (T4.2–T5.4 app layer)
- **Dependencies**: Requires Neo4j running on localhost:7687, data files present in `data/`
