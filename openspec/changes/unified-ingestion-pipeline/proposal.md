## Why

The current data ingestion process is fragmented across multiple steps, making it difficult to maintain context (such as the target of a modification) and leading to incomplete or inaccurate relationships. Furthermore, static relationships in `relation.parquet` are proving problematic or redundant. We need a unified pipeline that processes each document sequentially—loading the shell, extracting the preamble, parsing the structure, and dynamically extracting and ingesting relationships—to build a context-aware and robust Neo4j legal knowledge graph.

## What Changes

- Implement a single, unified pipeline script for document ingestion.
- Ingest document metadata (shells) into Neo4j, specifically filtering for `Thông tư`, `Nghị định`, `Luật`, `Bộ luật` issued from the year 2000 onwards.
- Extract the preamble (căn cứ) from documents and store it for future entity and context extraction.
- Parse the document body into hierarchical segments (Chapters, Articles, Clauses, Points) and ingest them into Neo4j.
- Dynamically extract internal, external, and modification cross-references using the extracted preamble context.
- Ingest these extracted relationships directly into the graph.
- Completely bypass and ignore the legacy `relation.parquet` file.

## Capabilities

### New Capabilities
- `unified-ingestion`: An end-to-end pipeline orchestrator that handles document ingestion from metadata to relationships.

### Modified Capabilities
- `segmentation`: The existing segmentation logic is now tightly integrated into the unified flow.
- `cross-reference-extraction`: Cross-reference extraction now operates dynamically within the pipeline rather than relying on pre-processed static files.

## Impact

- **Code:** Replaces fragmented ingestion scripts with a single orchestrator (`src/data_pipeline/full_ingest_neo4j.py` or similar).
- **Data Dependency:** Removes the dependency on `relation.parquet`.
- **Database:** Produces a more accurate, context-aware Neo4j graph with dynamically resolved `MODIFIES` and reference relationships.
