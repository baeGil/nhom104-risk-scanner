## ADDED Requirements

### Requirement: Mock embedding service
The system SHALL provide a MockEmbeddingService implementing the EmbeddingService interface that returns deterministic pseudo-random 1024-dimensional vectors for any input text. The same input text SHALL always produce the same vector (deterministic). The mock SHALL simulate processing delay of 10-50ms per text.

#### Scenario: Generate deterministic embedding
- **WHEN** mock embedder receives "test text"
- **THEN** it returns the same 1024-dim vector every time

#### Scenario: Simulate processing delay
- **WHEN** mock embedder processes a batch of texts
- **THEN** it delays 10-50ms per text to simulate real service

### Requirement: Mock graph traversal
The system SHALL provide a MockGraphTraversal implementing the GraphRepository interface that returns empty result lists for all traversal queries. The mock SHALL log all queries for debugging purposes.

#### Scenario: Return empty traversal results
- **WHEN** mock traversal is called for an Article
- **THEN** it returns an empty list without error

### Requirement: Mock effective text service
The system SHALL provide a MockEffectiveTextService that returns the Article.clean_text as the effective_text when EffectiveArticle nodes are not available. The mock SHALL set is_current=true and amendment_chain=[].

#### Scenario: Fallback to article clean text
- **WHEN** EffectiveArticle is not available
- **THEN** mock returns Article.clean_text as effective_text

### Requirement: Configuration-driven mock switching
The system SHALL allow switching between mock and real implementations via configuration in src/config.py. Settings SHALL include: EMBEDDING_SERVICE ("mock" | "real"), GRAPH_REPOSITORY ("mock" | "neo4j"), and EFFECTIVE_TEXT_SERVICE ("mock" | "real"). The default for development SHALL be "mock".

#### Scenario: Use mock by default
- **WHEN** config has EMBEDDING_SERVICE="mock"
- **THEN** system uses MockEmbeddingService

#### Scenario: Switch to real implementation
- **WHEN** config is changed to EMBEDDING_SERVICE="real"
- **THEN** system uses the real embedding service without code changes
