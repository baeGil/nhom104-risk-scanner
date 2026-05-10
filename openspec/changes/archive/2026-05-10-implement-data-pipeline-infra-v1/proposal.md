# Proposal: Data Pipeline Infrastructure v1

## Goal
Establish a robust, production-grade data processing pipeline for Vietnamese legal documents, enabling extraction, cleaning, and ingestion into a Neo4j knowledge graph.

## Scope
- **Normalization**: Standardizing `so_ky_hieu` and document metadata.
- **Crawling**: Refined crawler for retrieving missing content from thuvienphapluat.vn.
- **Cleaning**: HTML cleaning pipeline to strip unnecessary tags and preserve structure.
- **Ingestion**: Batch ingestion of document segments into Neo4j with hierarchy (Document -> Chapter -> Article -> Clause -> Point).

## Technical Implementation
- Python-based pipeline scripts in `src/data_pipeline/`.
- Neo4j as the primary graph database.
- Support for multiple document types (Luật, Nghị định, Thông tư).
