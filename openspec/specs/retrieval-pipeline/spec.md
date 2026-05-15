## ADDED Requirements

### Requirement: Multi-strategy retrieval engine
The system SHALL implement a retrieval engine that selects and executes the appropriate retrieval strategy based on the SubQuery.retrieval_strategy field from intent analysis. The engine SHALL support at minimum: direct_lookup, vector_search, graph_traversal, hybrid_search, validity_check, and comparison strategies.

#### Scenario: Route to direct lookup strategy
- **WHEN** SubQuery.retrieval_strategy is "direct_lookup"
- **THEN** the engine executes the DirectLookupStrategy

#### Scenario: Route to vector search strategy
- **WHEN** SubQuery.retrieval_strategy is "vector_search"
- **THEN** the engine executes the VectorSearchStrategy

#### Scenario: Route to hybrid search strategy
- **WHEN** SubQuery.retrieval_strategy is "hybrid_search"
- **THEN** the engine executes the HybridSearchStrategy combining fulltext and vector results

### Requirement: Direct lookup by article reference
For LOOKUP intent queries with specific article references (e.g., "Điều 17 Luật Doanh nghiệp 2020"), the system SHALL resolve the document reference to a doc_id via the so_ky_hieu lookup table, construct the Article UID using the convention "doc_{doc_id}_dieu_{index}", and retrieve the Article node with its parent Document metadata.

#### Scenario: Lookup specific article
- **WHEN** user asks "Điều 17 Luật Doanh nghiệp 2020 nói gì?"
- **THEN** system resolves "Luật Doanh nghiệp 2020" to doc_id, constructs uid "doc_{id}_dieu_17", and retrieves the Article

#### Scenario: Lookup with clause granularity
- **WHEN** user asks "Khoản 3 Điều 17 Luật Doanh nghiệp"
- **THEN** system retrieves the Article and returns the specific Clause by index

#### Scenario: Unresolved document reference
- **WHEN** so_ky_hieu cannot be resolved via lookup table
- **THEN** system returns an empty result with a flag indicating the reference could not be resolved

### Requirement: Vector similarity search
For TOPIC, SEARCH, SCENARIO, CHECKLIST, and NUMERIC intent queries, the system SHALL embed the query text using the vietlegal-harrier-0.6b model (1024 dimensions), perform a vector similarity search against the article_embeddings index in Neo4j using cosine similarity, retrieve the top-20 most similar Articles, and filter results by is_current=true and loai_van_ban priority.

#### Scenario: Topic query returns relevant articles
- **WHEN** user asks "Quy định về bảo hiểm xã hội"
- **THEN** system embeds the query, searches vector index, and returns top-20 Articles filtered by is_current

#### Scenario: Filter by document type priority
- **WHEN** vector search returns mixed document types
- **THEN** results are prioritized: Luật (3.0) > Nghị định (2.0) > Thông tư (1.5) > TTLT (1.0)

#### Scenario: Fallback to fulltext when embeddings unavailable
- **WHEN** embedding service is unavailable or article_embeddings index has no data
- **THEN** system falls back to fulltext search using article_fulltext index

### Requirement: Graph traversal for context expansion
From each matched Article, the system SHALL traverse: REFERENCES_INTERNAL to find related Articles within the same Document, REFERENCES_EXTERNAL to find cross-referenced Articles in other Documents, incoming MODIFIES edges to get EffectiveArticle nodes with current text, and DETAILS relationships to find implementing regulations (Nghị định, Thông tư).

#### Scenario: Expand context via internal references
- **WHEN** an Article has REFERENCES_INTERNAL relationships
- **THEN** the system retrieves all referenced Articles and includes them in the result set

#### Scenario: Get effective text via MODIFIES traversal
- **WHEN** an Article has incoming MODIFIES edges
- **THEN** the system retrieves the EffectiveArticle with is_current=true

#### Scenario: Empty traversal when no relationships exist
- **WHEN** an Article has no cross-reference relationships
- **THEN** traversal returns an empty list without error

### Requirement: Authority-weighted reranking
The system SHALL combine retrieval scores using the formula: combined_score = semantic_score × authority_weight × graph_boost. Authority weights SHALL be: Luật (3.0), Nghị định (2.0), Thông tư (1.5), TTLT (1.0). Articles discovered via graph traversal SHALL receive a 1.5× graph boost. The system SHALL return the top-5 provisions per query after reranking.

#### Scenario: Rerank boosts Luật over Thông tư
- **WHEN** semantic scores are equal for a Luật article and a Thông tư article
- **THEN** the Luật article ranks higher due to authority weight (3.0 vs 1.5)

#### Scenario: Graph traversal boost
- **WHEN** an Article is found via graph traversal from a directly matched Article
- **THEN** its score is multiplied by 1.5× graph boost

#### Scenario: Return top-5 after reranking
- **WHEN** retrieval returns 20 candidates
- **THEN** system returns only the top-5 after reranking

### Requirement: Validity check strategy
For VALIDITY intent queries, the system SHALL look up the specified Article or Document, check its is_current flag, check for incoming SUPERSEDED_BY relationships, and return the validity status with the effective date and superseding document if applicable.

#### Scenario: Check article validity
- **WHEN** user asks "Điều 50 Luật Đất đai 2013 còn hiệu lực không?"
- **THEN** system retrieves the Article, checks is_current, and returns validity status

#### Scenario: Document superseded
- **WHEN** a Document has SUPERSEDED_BY relationships
- **THEN** system returns the superseding document information

### Requirement: Comparison strategy
For COMPARISON intent queries, the system SHALL perform parallel direct lookups for each document/article pair specified in the query, retrieve both versions, and return them side-by-side with a diff of changes.

#### Scenario: Compare two law versions
- **WHEN** user asks "So sánh Luật Doanh nghiệp 2014 và 2020"
- **THEN** system retrieves both versions and returns them with a diff

### Requirement: RetrievedProvision output format
Each retrieved provision SHALL include: the Article node (uid, index, title, clean_text), the EffectiveArticle node if available (effective_text, amendment_chain, is_current), the parent Document metadata (so_ky_hieu, title, loai_van_ban, ngay_ban_hanh), the combined reranking score, and the retrieval strategy that found it.

#### Scenario: Output includes all required fields
- **WHEN** retrieval completes
- **THEN** each RetrievedProvision contains article, effective_article (if available), document, score, and strategy
