## ADDED Requirements

### Requirement: QA-first sub-query planning
The system SHALL normalize intent analysis output into QA-first sub-queries for pure legal questions. LOOKUP intents SHALL produce direct lookup sub-queries, TOPIC/SEARCH/SCENARIO/CHECKLIST/NUMERIC intents SHALL produce hybrid search sub-queries, and VALIDITY intents SHALL produce best-effort validity sub-queries.

#### Scenario: Plan direct lookup
- **WHEN** intent analysis identifies a LOOKUP intent with an article reference
- **THEN** the system creates a SubQuery with retrieval_strategy="direct_lookup"

#### Scenario: Plan topic retrieval
- **WHEN** intent analysis identifies a TOPIC, SEARCH, SCENARIO, CHECKLIST, or NUMERIC intent
- **THEN** the system creates a SubQuery with retrieval_strategy="hybrid_search"

#### Scenario: Plan best-effort validity
- **WHEN** intent analysis identifies a VALIDITY intent
- **THEN** the system creates a SubQuery with retrieval_strategy="validity_check" and marks validity as best-effort

### Requirement: Pure QA routing priority
The system SHALL route QA-domain questions through the legal QA pipeline before considering contract-review-specific flows. CONTRACT_QA and CONTRACT_REVIEW domains SHALL remain out of scope for the initial Phase 5 implementation unless explicitly invoked by the caller.

#### Scenario: Route QA domain
- **WHEN** intent analysis returns domain="QA"
- **THEN** the system routes the request to the legal QA pipeline

#### Scenario: Defer contract QA
- **WHEN** intent analysis returns domain="CONTRACT_QA"
- **THEN** the system does not use the pure QA pipeline unless the caller explicitly supports contract context
