## MODIFIED Requirements

### Requirement: Match clauses to legal provisions
For each extracted clause, the system SHALL find relevant legal provisions using query rewrite followed by hybrid retrieval across Article, Clause, and Point legal segments. Retrieval SHALL combine vector search, full-text search, exact keyword/title matching, REFERENCES expansion, MODIFIES validity signals, and reranking. The system SHALL return top-5 provisions per clause with complete Document → Article → Clause → Point context when available.

#### Scenario: Match penalty clause to law
- **WHEN** clause is about penalty limits
- **THEN** system returns provisions from applicable commercial or civil law with article, clause, or point context when available

#### Scenario: Match point-level provision
- **WHEN** a point-level legal segment is the best match
- **THEN** system returns the point along with its parent clause, article, and document title

### Requirement: Analyze compliance with legal provisions
For each clause with matched provisions, the system SHALL generate a compliance report using the LLM with context including: clause text, matched legal provisions, assembled Article/Clause/Point context, document metadata, REFERENCES context, and MODIFIES validity signals. Output SHALL include violations, risks, suggestions, and precise citation objects that contain both display text and graph uid.

#### Scenario: Detect penalty violation
- **WHEN** clause penalty exceeds legal limit
- **THEN** system reports violation with citation

#### Scenario: Include validity warning
- **WHEN** a matched provision has MODIFIES context indicating possible amendment
- **THEN** system includes that validity signal in the compliance context or report

### Requirement: Verify all citations
Every citation in the compliance report SHALL be verified against Neo4j using the cited graph uid as the primary key and citation text as a consistency check. Citations SHALL be marked as VERIFIED when the uid exists and the hierarchy metadata matches the display citation, or UNVERIFIED with a reason when validation fails. Target: 100% of citations verified or explicitly flagged.

#### Scenario: Verify citation exists
- **WHEN** citation references a real legal segment uid
- **THEN** it is marked VERIFIED

#### Scenario: Flag mismatched citation text
- **WHEN** citation display text names a different article, clause, point, or document than the referenced uid
- **THEN** it is marked UNVERIFIED with a mismatch reason

## ADDED Requirements

### Requirement: OCR scanned contracts using GPT-4o-mini
The system SHALL support GPT-4o-mini OCR for scanned PDFs or image-based contract pages. The parser SHALL use direct text extraction for TXT, MD, and text-layer PDFs before falling back to OCR.

#### Scenario: OCR scanned PDF
- **WHEN** a PDF page has insufficient extractable text
- **THEN** the system sends page images to GPT-4o-mini OCR and returns Markdown or plain text for downstream clause extraction

### Requirement: Persist contract review outputs
The system SHALL persist contract jobs, extracted clauses, legal matches, compliance results, and citation verification outcomes in application storage. The legal Neo4j graph SHALL remain the source for legal data and SHALL NOT store user-uploaded contract content as legal graph nodes.

#### Scenario: Retrieve completed job
- **WHEN** a completed contract review job is requested after backend restart
- **THEN** the system returns the persisted clauses, matches, compliance results, and citation verification statuses
