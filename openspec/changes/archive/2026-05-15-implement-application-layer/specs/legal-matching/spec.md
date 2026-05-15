## ADDED Requirements

### Requirement: Match contract clauses to legal provisions
For each ContractClause, the system SHALL find the most relevant legal provisions using a three-step process: (A) semantic search via vector similarity or fulltext search, (B) graph traversal to expand context from matched Articles, and (C) reranking by combined score.

#### Scenario: Match clause to relevant law
- **WHEN** clause text is "Phạt 30% giá trị hợp đồng khi vi phạm"
- **THEN** system returns provisions from Luật Thương mại regarding penalty limits

#### Scenario: Return top-5 provisions per clause
- **WHEN** semantic search returns 20 candidates
- **THEN** system returns only the top-5 after reranking

### Requirement: Semantic search with fallback
The system SHALL first attempt vector similarity search using the ContractClause.embedding against the article_embeddings index. If the embedding service is unavailable or the vector index has no data, the system SHALL fall back to fulltext search using the article_fulltext index on Article.title and Article.clean_text.

#### Scenario: Vector search when available
- **WHEN** embedding service is running and articles have embeddings
- **THEN** system uses vector similarity search

#### Scenario: Fulltext fallback when embeddings unavailable
- **WHEN** embedding service is down or no embeddings exist
- **THEN** system uses fulltext search as fallback

### Requirement: Authority-weighted reranking
The system SHALL rerank matched provisions using: combined_score = semantic_score × authority_weight × graph_boost. Authority weights: Luật (3.0), Nghị định (2.0), Thông tư (1.5), TTLT (1.0). Graph traversal boost: 1.5× for articles found via cross-reference traversal.

#### Scenario: Prioritize Luật over Thông tư
- **WHEN** both a Luật and a Thông tư article have similar semantic scores
- **THEN** the Luật article ranks higher

### Requirement: Filter by validity and relevance
The system SHALL filter results to include only Articles with is_current=true, prioritize by loai_van_ban (Luật > Nghị định > Thông tư > TTLT), and filter by nganh/linh_vuc relevance to the contract type when metadata is available.

#### Scenario: Exclude superseded provisions
- **WHEN** vector search returns an Article with is_current=false
- **THEN** that Article is excluded from results
