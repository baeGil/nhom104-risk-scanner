## MODIFIED Requirements

### Requirement: Parse hierarchical segments
The system SHALL parse document content into Chapters, Articles, Clauses, and Points, linking them to their parent Document node, executing this directly as stage 3 of the unified pipeline.

#### Scenario: Parsing document structure
- **WHEN** the parser processes a document's HTML content during the pipeline execution
- **THEN** it creates the segment nodes and the HAS_CHAPTER, HAS_ARTICLE, HAS_CLAUSE, HAS_POINT relationships directly in Neo4j.
