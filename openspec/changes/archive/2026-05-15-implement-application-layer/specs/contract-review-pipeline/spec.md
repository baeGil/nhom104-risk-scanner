## ADDED Requirements

### Requirement: Extract contract clauses using LLM
The system SHALL use the LLM to extract structured clauses from contract Markdown text produced by the contract parser. Each extracted clause SHALL include: clause index, clause_type (from predefined types: thanh_toán, bảo_hành, phạt, chấm_dứt, bồi_thường, bảo_mật, giải_quyết_tranh_chấp, force_majeure), text_content, parties_involved, obligations, amount (if present), and deadline (if present). Clause embeddings SHALL be generated using vietlegal-harrier-0.6b (1024 dimensions). Target accuracy: ≥90% on test contracts.

#### Scenario: Extract payment clause
- **WHEN** contract text contains a payment clause
- **THEN** system extracts it with type="thanh_toán" and amount

#### Scenario: Generate clause embeddings
- **WHEN** clauses are extracted
- **THEN** each clause has a 1024-dimensional embedding

### Requirement: Match clauses to legal provisions
For each extracted clause, the system SHALL find relevant legal provisions using vector similarity search (top-20), filter by is_current=true and document type priority, expand context via graph traversal, rerank by combined score (semantic × authority × graph_boost), and return top-5 provisions per clause.

#### Scenario: Match penalty clause to law
- **WHEN** clause is about penalty limits
- **THEN** system returns provisions from Luật Thương mại regarding penalties

### Requirement: Analyze compliance with legal provisions
For each clause with matched provisions, the system SHALL generate a compliance report using the LLM with context including: clause text, matched provisions (EffectiveArticle text), amendment history, document metadata, and detailing regulations. Output SHALL include violations, risks, suggestions, and precise citations.

#### Scenario: Detect penalty violation
- **WHEN** clause penalty exceeds legal limit
- **THEN** system reports violation with citation

### Requirement: Verify all citations
Every citation in the compliance report SHALL be verified against Neo4j. Citations SHALL be marked as VERIFIED (article exists, document exists, is_current=true) or UNVERIFIED (with reason). Target: 100% of citations verified or explicitly flagged.

#### Scenario: Verify citation exists
- **WHEN** citation references a real article
- **THEN** it is marked VERIFIED

### Requirement: Classify policy compliance
For policy documents, the system SHALL classify each provision as: "compliant_and_efficient", "compliant_but_restrictive" (exceeds legal requirements), or "non_compliant". Provisions more restrictive than law SHALL be flagged with explanation.

#### Scenario: Flag overly restrictive policy
- **WHEN** policy exceeds legal requirements
- **THEN** it is classified as "compliant_but_restrictive"
