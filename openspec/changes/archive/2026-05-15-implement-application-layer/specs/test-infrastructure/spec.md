## ADDED Requirements

### Requirement: Shared test fixtures via conftest.py
The system SHALL provide a root conftest.py with shared pytest fixtures including: sample contract texts (valid PDF text, DOCX text, TXT text), sample legal questions (LOOKUP, TOPIC, VALIDITY, COMPARISON intents), mock Neo4j driver fixture, mock LLM client fixture, mock embedding service fixture, and sample PII test texts for each PII type (CCCD, MST, phone, email, bank, address).

#### Scenario: Use mock LLM fixture
- **WHEN** a test uses the mock_llm fixture
- **THEN** it receives a MockLLMProvider that returns predefined responses

#### Scenario: Use sample contract fixture
- **WHEN** a test uses the sample_contract fixture
- **THEN** it receives a Contract object with known content for testing

### Requirement: Pytest configuration
The system SHALL provide a pytest.ini file configuring: testpaths to include src/*/tests, markers for skip_if_no_neo4j, skip_if_no_llm, skip_if_no_embedding, asyncio_mode for async tests, and verbose output by default.

#### Scenario: Run tests with markers
- **WHEN** tests are run with pytest -m "not skip_if_no_neo4j"
- **THEN** Neo4j-dependent tests are skipped

### Requirement: Mock LLM provider
The system SHALL provide a MockLLMProvider implementing the LLMClient interface with predefined responses for known query patterns. For unknown queries, it SHALL return a generic fallback response. The mock SHALL support: intent_analysis responses (with domain, intents, sub_queries), clause_extraction responses (with clause arrays), compliance_analysis responses (with violations, risks, suggestions), and answer_generation responses (with answer text and citations).

#### Scenario: Return predefined intent response
- **WHEN** mock receives "Điều 17 Luật Doanh nghiệp"
- **THEN** it returns LOOKUP intent with article=17

#### Scenario: Return fallback for unknown query
- **WHEN** mock receives an unrecognized query
- **THEN** it returns a generic response with low confidence

### Requirement: Async test support
All async tests SHALL use pytest-asyncio with @pytest.mark.asyncio decorator. The system SHALL NOT use the deprecated asyncio.get_event_loop().run_until_complete() pattern.

#### Scenario: Run async test
- **WHEN** an async test is decorated with @pytest.mark.asyncio
- **THEN** pytest executes it correctly with async event loop
