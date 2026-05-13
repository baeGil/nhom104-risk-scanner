## ADDED Requirements

### Requirement: Apply Neo4j Schema
The system SHALL apply the Neo4j schema from `output/neo4j_schema.cypher` before any data ingestion. This includes uniqueness constraints, property indexes, fulltext indexes, and the vector index for Article embeddings.

#### Scenario: Schema applied successfully
- **WHEN** the schema script is executed against a fresh Neo4j instance
- **THEN** all 5 uniqueness constraints SHALL be created (Document.id, Article.uid, Clause.uid, Point.uid, EffectiveArticle.uid)
- **AND** all property indexes SHALL be created
- **AND** all 3 fulltext indexes SHALL be created
- **AND** the vector index `article_embeddings` SHALL be created with 1024 dimensions and cosine similarity

#### Scenario: Schema is idempotent
- **WHEN** the schema script is executed a second time
- **THEN** no errors SHALL occur because all statements use IF NOT EXISTS

### Requirement: Ingest Document Nodes
The system SHALL ingest all Document nodes from `data/metadata_deduped.parquet` into Neo4j using batch MERGE operations.

#### Scenario: Ingest all Document nodes
- **WHEN** the ingest script is run with metadata_deduped.parquet containing 21,000 records
- **THEN** exactly 21,000 Document nodes SHALL exist in Neo4j
- **AND** each node SHALL have properties: id, so_ky_hieu, title, loai_van_ban, ngay_ban_hanh, tinh_trang_hieu_luc, co_quan_ban_hanh, nganh, linh_vuc

#### Scenario: Batch processing
- **WHEN** ingesting Document nodes
- **THEN** nodes SHALL be processed in batches of 5,000 using UNWIND
- **AND** each batch SHALL use MERGE on Document.id for idempotency

#### Scenario: Re-run produces same result
- **WHEN** the ingest script is run a second time
- **THEN** the Document node count SHALL remain unchanged (no duplicates created)

### Requirement: Ingest Document Relationships
The system SHALL ingest all document-level relationships from `data/relationships.parquet` into Neo4j using batch MERGE operations with relationship type mapping.

#### Scenario: Ingest all relationships
- **WHEN** the ingest script is run with relationships.parquet containing 659,000 records
- **THEN** all valid relationships SHALL be created in Neo4j
- **AND** relationship types SHALL include: CITES, REFERRED_BY, DETAILS, DETAILED_BY, SUPERSEDES, SUPERSEDED_BY, PARTIALLY_SUPERSEDES, PARTIALLY_SUPERSEDED_BY, AMENDS, AMENDED_BY, SUPPLEMENTS, SUPPLEMENTED_BY, RELATED, SUSPENDS, SUSPENDED_BY, PARTIALLY_SUSPENDS, PARTIALLY_SUSPENDED_BY

#### Scenario: Skip orphan relationships
- **WHEN** a relationship references a Document ID that does not exist in Neo4j
- **THEN** that relationship SHALL be skipped
- **AND** the orphan Document IDs SHALL be logged to `output/orphan_relationships.json`

#### Scenario: Batch processing
- **WHEN** ingesting relationships
- **THEN** relationships SHALL be grouped by type and processed in batches of 5,000 using UNWIND
- **AND** each batch SHALL use MERGE for idempotency

### Requirement: Validate Ingestion
The system SHALL validate the ingestion results by comparing Neo4j node/relationship counts against source data.

#### Scenario: Validate Document count
- **WHEN** ingestion is complete
- **THEN** the Document node count in Neo4j SHALL equal the row count in metadata_deduped.parquet

#### Scenario: Validate relationship count
- **WHEN** ingestion is complete
- **THEN** the total relationship count in Neo4j SHALL equal the valid (non-orphan) row count in relationships.parquet
