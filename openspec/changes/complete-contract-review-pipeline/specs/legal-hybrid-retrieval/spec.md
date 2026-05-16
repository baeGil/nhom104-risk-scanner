## ADDED Requirements

### Requirement: Rewrite contract clauses into legal retrieval plans
The system SHALL rewrite each extracted contract clause into a structured legal retrieval plan before searching the legal graph. The plan SHALL include the original clause text, legal_issue, rewritten search_queries, keywords, expected_domains or title_hints, risk_type, and optional filters such as document type.

#### Scenario: Rewrite penalty clause
- **WHEN** a contract clause states that the violating party must pay a 30% penalty
- **THEN** the system produces rewritten queries and keywords related to penalty limits, contractual penalties, and applicable commercial law provisions

### Requirement: Search embedded Article, Clause, and Point nodes
The system SHALL perform vector retrieval over legal segments that include Article, Clause, and Point nodes with embeddings. Search results SHALL include uid, labels, score, text, document metadata, and hierarchy path sufficient to assemble a citation.

#### Scenario: Return point-level result
- **WHEN** the most relevant provision is a Point node
- **THEN** the retrieval result includes the Point uid and enough parent context to identify its Clause, Article, and Document

### Requirement: Combine vector, full-text, exact, and graph candidates
The system SHALL perform hybrid retrieval by merging candidates from vector search, full-text search, exact keyword/title matching, and graph expansion. Candidate merging SHALL deduplicate by uid and preserve source scores for reranking.

#### Scenario: Merge duplicate candidate
- **WHEN** the same legal segment is returned by vector search and full-text search
- **THEN** the system keeps one candidate with both score sources recorded

### Requirement: Expand retrieval context through references and modifications
The system SHALL expand high-confidence candidates through outgoing and incoming REFERENCES and MODIFIES relationships. REFERENCES edges SHALL preserve internal/external type metadata when present, and MODIFIES edges SHALL be used to produce validity signals.

#### Scenario: Expand from referenced provision
- **WHEN** a candidate references another legal segment
- **THEN** the referenced segment is included as graph context with a graph expansion score

#### Scenario: Flag modified provision
- **WHEN** a matched provision has related MODIFIES edges
- **THEN** the retrieval output includes a validity signal indicating that the provision may be modified or not the latest known text

### Requirement: Rerank legal candidates with transparent score factors
The system SHALL rerank merged candidates using semantic score, lexical score, exact-match boost, authority weight, graph boost, validity signal, and title/domain match. The final top results SHALL expose score factors for debugging and evaluation.

#### Scenario: Prefer exact legal phrase match
- **WHEN** two candidates have similar semantic scores but one contains an exact rewritten legal keyword
- **THEN** the exact-match candidate receives a higher combined score

### Requirement: Assemble complete legal context for matched segments
For every returned match, the system SHALL assemble the fullest available context from Document title down through Article, Clause, and Point. The assembled context SHALL include display citation text and stable graph uid.

#### Scenario: Assemble clause context
- **WHEN** a Clause node is matched
- **THEN** the response includes its parent Article, Document title, clause text, and display citation
