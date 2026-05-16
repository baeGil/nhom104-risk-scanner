## ADDED Requirements

### Requirement: QA citation verification by UID
The system SHALL verify QA answer citations by graph UID before relying on display text parsing. For each citation with a uid, the verifier SHALL resolve the graph node, check article/clause/point metadata when provided, and return verification status and reason.

#### Scenario: Verify citation uid
- **WHEN** a QA answer citation includes a uid that exists in Neo4j
- **THEN** the citation is marked VERIFIED with the resolved article uid and document title

#### Scenario: Missing citation uid
- **WHEN** a QA answer citation does not include a uid
- **THEN** the verifier falls back to Vietnamese citation text parsing

#### Scenario: Citation metadata mismatch
- **WHEN** the citation uid exists but article, clause, point, or document title does not match the graph context
- **THEN** the citation is marked UNVERIFIED with a mismatch reason

### Requirement: QA answer verification summary
The system SHALL attach citation verification results to the final QA JSON response. The summary SHALL include per-citation status and an aggregate flag indicating whether all citations are verified.

#### Scenario: All citations verified
- **WHEN** every QA citation is verified
- **THEN** the QA response includes citations_verified=true

#### Scenario: Some citations unverified
- **WHEN** one or more QA citations are unverified
- **THEN** the QA response includes citations_verified=false and per-citation reasons
