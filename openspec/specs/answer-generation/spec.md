## ADDED Requirements

### Requirement: Answer generation with legal context
The system SHALL generate answers to legal questions by assembling a prompt containing the user question, retrieved legal provisions (Article text), effective text (EffectiveArticle.effective_text if available), and amendment history. The system SHALL use the LLM with the answer_generation prompt template and parse the response as JSON containing an answer string and citations array.

#### Scenario: Generate answer with retrieved provisions
- **WHEN** user asks "Điều 17 Luật Doanh nghiệp quy định gì?" and retrieval returns matching provisions
- **THEN** system assembles prompt with question + provisions + effective text and generates an answer

#### Scenario: Include amendment history in context
- **WHEN** the retrieved Article has been modified by other documents
- **THEN** the amendment history is included in the prompt context

#### Scenario: Fallback when no provisions found
- **WHEN** retrieval returns no matching provisions
- **THEN** system generates a response indicating no relevant provisions were found

### Requirement: Structured answer output
The LLM output SHALL be parsed as JSON with the structure: { "answer": string, "citations": [ { "document": string, "article": string, "clause": string (optional), "point": string (optional), "text": string } ] }. The answer SHALL be in Vietnamese and include precise citations in the format "Điều X khoản Y Luật/ND/TT Z".

#### Scenario: Parse answer with citations
- **WHEN** LLM returns a valid JSON response
- **THEN** system extracts the answer text and citations array

#### Scenario: Invalid JSON response
- **WHEN** LLM returns non-JSON or malformed JSON
- **THEN** system retries once, then returns the raw text with a warning

### Requirement: Streaming answer delivery
The system SHALL stream the answer text token-by-token via SSE to the frontend, sending intents and provisions as separate SSE chunks when available, and terminating the stream with data: [DONE].

#### Scenario: Stream answer token by token
- **WHEN** answer generation begins
- **THEN** tokens are sent incrementally via SSE with data: prefix

#### Scenario: Send metadata mid-stream
- **WHEN** intents and provisions are available
- **THEN** they are sent as a separate SSE chunk without token field
