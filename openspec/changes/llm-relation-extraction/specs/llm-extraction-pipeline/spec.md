## ADDED Requirements

### Requirement: Extract Waterfall Context
The system SHALL extract waterfall context from Neo4j for a given document by concatenating the `clean_text` property of Article, Clause, and Point nodes in their hierarchical order.

#### Scenario: Full hierarchy node
- **WHEN** a leaf node is a Point
- **THEN** the context string is the concatenation of its parent Article's `clean_text`, its parent Clause's `clean_text`, and its own `clean_text`.

#### Scenario: Partial hierarchy node
- **WHEN** a leaf node is a Clause (has no child Points)
- **THEN** the context string is the concatenation of its parent Article's `clean_text` and its own `clean_text`.

### Requirement: Batching Strategy
The system SHALL batch leaf nodes together before sending to the LLM to optimize API calls, using a customizable limit (e.g. word count or token limit).

#### Scenario: Batching by word limit
- **WHEN** processing nodes sequentially
- **THEN** the system accumulates nodes until the total combined text length reaches the predefined batch limit, then groups them as a single prompt payload.

### Requirement: Enforce JSON Schema
The system SHALL prompt the LLM to return exactly a predefined JSON schema containing `action_type`, `target_document`, `target_article`, `target_clause`, `target_point`, and `quote_context`.

#### Scenario: Successful schema enforcement
- **WHEN** the LLM returns the parsed result
- **THEN** the result strictly matches the predefined schema and returns an array of relationships mapped to the original `uid` of the node.

### Requirement: Prompt Rules Execution
The LLM prompt SHALL include specific legal rules: Rule of Title, Rule of Passive History, Rule of Enumeration, and Rule of Context Override.

#### Scenario: Handling Enumeration
- **WHEN** the input text specifies "Điều 1, 2 và 3 của Luật Thuế"
- **THEN** the LLM returns three separate relationship objects for each target article.

#### Scenario: Handling Passive History
- **WHEN** the input text describes an action in passive voice (e.g., "đã được sửa đổi")
- **THEN** the LLM does not classify this as an active modification action.
