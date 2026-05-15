## ADDED Requirements

### Requirement: Interactive Testing Interface
The system SHALL provide a test script or Jupyter notebook interface to test the LLM extraction pipeline on a specific Document ID.

#### Scenario: Running test on a document
- **WHEN** a developer executes the test script with a target `doc_id`
- **THEN** the script fetches the nodes, applies the LLM extraction, and prints out the parsed JSON for human review without writing modifications back to the graph.

### Requirement: Granular Node Testing
The system SHALL allow developers to test the prompt against specific hard-coded or queried leaf nodes (e.g. testing Article 87 specifically).

#### Scenario: Debugging a tricky node
- **WHEN** a developer provides a specific `uid` or hardcoded text snippet
- **THEN** the script bypasses batching, sends only that snippet to the LLM with the prompt, and returns the result for fast debugging.
