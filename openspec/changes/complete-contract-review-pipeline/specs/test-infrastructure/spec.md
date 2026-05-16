## ADDED Requirements

### Requirement: Golden contract review fixtures
The system SHALL include golden contract review fixtures containing sample contract text, expected extracted clauses, expected risk categories, and expected relevant legal segment uids or document titles.

#### Scenario: Run golden fixture
- **WHEN** the golden contract test suite runs
- **THEN** each fixture validates clause extraction, retrieval expectations, and compliance output structure

### Requirement: Hybrid retrieval evaluation
The system SHALL include retrieval evaluation tests that measure whether expected legal segments appear in top-k results for labeled contract clauses. The tests SHALL report precision@k or hit@k for vector-only, lexical-only, and hybrid retrieval when practical.

#### Scenario: Expected provision appears in top five
- **WHEN** a labeled penalty clause is retrieved
- **THEN** the expected legal segment or expected legal document appears in the top five hybrid results

### Requirement: Citation verification tests
The system SHALL include tests for citation verification using valid graph uids, invalid graph uids, and mismatched citation display text.

#### Scenario: Invalid uid is unverified
- **WHEN** citation verification receives a uid that does not exist in Neo4j
- **THEN** the citation is marked UNVERIFIED with a reason

### Requirement: Contract API smoke tests
The system SHALL include API smoke tests for uploading a contract, polling job status, receiving completed results, and retrieving job history. Tests that require live LLM, OCR, or Neo4j SHALL be marked so they can be skipped in local fast test runs.

#### Scenario: Complete contract review smoke test
- **WHEN** a valid TXT contract is uploaded in an integration environment
- **THEN** the API eventually returns completed status with clauses, matches, compliance, and citation verification fields

### Requirement: Frontend contract review rendering tests
The system SHALL include frontend tests or fixtures that verify real API-shaped contract review results render clause cards, legal matches, compliance violations, and citation badges without relying on legacy mock-only data shapes.

#### Scenario: Render completed job
- **WHEN** the frontend receives a completed job response with clauses, matches, compliance, and citations
- **THEN** it displays the result without missing required fields or layout-breaking errors
