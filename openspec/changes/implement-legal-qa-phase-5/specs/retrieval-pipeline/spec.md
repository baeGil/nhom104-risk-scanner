## MODIFIED Requirements

### Requirement: Vector similarity search
For TOPIC, SEARCH, SCENARIO, CHECKLIST, and NUMERIC intent queries, the system SHALL use the Phase 4 hybrid legal segment retrieval core. Retrieval SHALL search embedded legal segments across Article, Clause, and Point nodes when the LegalSegment retrieval indexes are available, and SHALL include the original query plus rewritten legal search terms when applicable.

#### Scenario: Topic query returns relevant legal segments
- **WHEN** user asks "Quy định về bảo hiểm xã hội"
- **THEN** system searches legal segments and returns relevant Article, Clause, or Point candidates with parent Document context

#### Scenario: Filter by document type priority
- **WHEN** vector search returns mixed document types
- **THEN** results are prioritized: Luật (3.0) > Nghị định (2.0) > Thông tư (1.5) > TTLT (1.0)

#### Scenario: Fallback to fulltext when embeddings unavailable
- **WHEN** embedding service is unavailable or vector indexes have no data
- **THEN** system falls back to fulltext search over legal segment text and titles

### Requirement: Graph traversal for context expansion
From each matched legal segment, the system SHALL use available graph relationships to add context. The traversal SHALL support the current graph shape using `REFERENCES` and `MODIFIES` relationships when present, and SHALL tolerate missing `DETAILS`, `SUPERSEDES`, or EffectiveArticle data without failing the QA request.

#### Scenario: Expand context via references
- **WHEN** a matched legal segment has REFERENCES relationships
- **THEN** the system retrieves referenced legal segments and includes relationship metadata in the result

#### Scenario: Surface modification signal
- **WHEN** a matched legal segment has related MODIFIES relationships
- **THEN** the system includes a validity signal indicating the provision may have been modified

#### Scenario: Empty traversal when no relationships exist
- **WHEN** a matched legal segment has no cross-reference relationships
- **THEN** traversal returns an empty context list without error

### Requirement: Validity check strategy
For VALIDITY intent queries, the system SHALL perform a best-effort lookup of the specified Article, Clause, Point, or Document and return a validity object with status, reason, and supporting evidence. Status values SHALL be `verified`, `likely_current`, or `unknown`.

#### Scenario: Verified current status
- **WHEN** the graph contains explicit is_current or EffectiveArticle evidence for the target provision
- **THEN** the system returns validity.status="verified" with supporting evidence

#### Scenario: Incomplete relationship data
- **WHEN** the graph does not contain enough relationship or effective-text evidence
- **THEN** the system returns validity.status="unknown" with a reason explaining the missing evidence

#### Scenario: Possible modification signal
- **WHEN** MODIFIES relationships indicate the target may have been changed but effective text is unavailable
- **THEN** the system returns validity.status="likely_current" or "unknown" with a modification warning

### Requirement: RetrievedProvision output format
Each retrieved provision SHALL include a stable uid, segment type, text, display citation, parent Article path, parent Document metadata, retrieval score, retrieval strategy, source score factors when available, references context, modifies context, and best-effort validity signal. Effective text SHALL be included when available; otherwise the provision text SHALL be used with a validity note.

#### Scenario: Output includes all required fields
- **WHEN** retrieval completes
- **THEN** each RetrievedProvision contains uid, segment_type, text, citation, document, score, strategy, and validity signal

#### Scenario: Effective text unavailable
- **WHEN** no EffectiveArticle exists for a retrieved provision
- **THEN** the system returns the provision text and marks effective_text_status as unavailable or fallback
