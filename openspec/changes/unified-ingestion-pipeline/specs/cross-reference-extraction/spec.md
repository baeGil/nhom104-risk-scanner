## MODIFIED Requirements

### Requirement: Extract internal references
The system SHALL extract internal references dynamically within the unified pipeline.

#### Scenario: Internal ref extraction
- **WHEN** an article text contains internal reference language
- **THEN** the system extracts and creates a REFERENCES_INTERNAL relationship.

### Requirement: Extract external references
The system SHALL extract external references using a global lookup table dynamically within the unified pipeline.

#### Scenario: External ref extraction
- **WHEN** an article cites another document
- **THEN** it resolves the document ID and creates a REFERENCES_EXTERNAL relationship.

### Requirement: Extract modification references
The system SHALL extract modification references using the preamble context to identify the primary target document when the target is implicit.

#### Scenario: Modification extraction with context
- **WHEN** an article states "sửa đổi Điều X" without naming a document AND preamble context has a Primary Target
- **THEN** the system links the MODIFIES relationship to Article X of the Primary Target document.
