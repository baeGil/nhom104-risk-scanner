## MODIFIED Requirements

### Requirement: Structured answer output
The LLM output SHALL be parsed as strict JSON with the structure: `{ "answer": string, "citations": [citation], "retrieved_provisions": [provision], "intent": object, "confidence": number, "validity": object }`. Each citation SHALL include `display_text`, `uid`, `document_title`, `article`, `clause`, and `point` fields when available. The answer SHALL be in Vietnamese and SHALL only cite retrieved provisions.

#### Scenario: Parse answer with citations
- **WHEN** LLM returns a valid JSON response
- **THEN** system extracts answer, citations, retrieved_provisions, intent, confidence, and validity fields

#### Scenario: Invalid JSON response
- **WHEN** LLM returns non-JSON or malformed JSON
- **THEN** system retries once, then returns a structured error response with the raw text and warning metadata

#### Scenario: Citation uses retrieved UID
- **WHEN** answer generation includes a citation
- **THEN** the citation uid matches one of the retrieved provision uids

## ADDED Requirements

### Requirement: Backend-oriented QA answer object
The system SHALL return a backend-oriented QA answer object after answer generation. The object SHALL be suitable for downstream persistence, API response formatting, and citation verification without reparsing natural-language answer text.

#### Scenario: Return processable answer object
- **WHEN** answer generation completes
- **THEN** the system returns a JSON-compatible object containing answer text, citations, retrieved provision metadata, intent metadata, and validity metadata

### Requirement: No-provision answer handling
When retrieval returns no provisions, the system SHALL return a structured QA answer explaining that no relevant provision was found. The response SHALL include an empty citations array and a retrieval status that distinguishes no results from pipeline failure.

#### Scenario: No provisions found
- **WHEN** retrieval returns no matching provisions
- **THEN** the system returns an answer object with citations=[], retrieved_provisions=[], and retrieval_status="no_results"
