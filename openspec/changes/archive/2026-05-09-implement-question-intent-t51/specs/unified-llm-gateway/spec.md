## ADDED Requirements

### Requirement: Unified LLM client interface
The system SHALL provide a unified LLMClient abstract class with methods: chat(prompt, schema) → JSON, extract(text, schema) → StructuredData, and classify(text, categories) → Category + confidence. The client SHALL support configurable providers (OpenAI, Claude, local) and a Mock provider for development/testing.

#### Scenario: Use OpenAI provider
- **WHEN** LLMClient is configured with OpenAI provider
- **THEN** chat() calls OpenAI API and returns structured JSON

#### Scenario: Use Mock provider for testing
- **WHEN** LLMClient is configured with Mock provider
- **THEN** chat() returns predefined fixture data without API calls

#### Scenario: Switch providers
- **WHEN** provider configuration changes from OpenAI to Claude
- **THEN** all LLM calls use Claude API without code changes

### Requirement: Structured JSON output
The system SHALL produce structured JSON output from LLM calls following a defined schema. The schema SHALL include: conversation_id, turn_number, domain, confidence, intents[], sub_queries[], context_references, and routing.

#### Scenario: Valid JSON output
- **WHEN** LLM processes a query
- **THEN** output is valid JSON matching the defined schema

#### Scenario: Schema validation
- **WHEN** LLM output does not match schema
- **THEN** system retries with schema enforcement prompt

### Requirement: Intent analysis via LLM
The system SHALL use LLM to analyze user queries and produce IntentClassification results. The analysis SHALL include: domain classification, intent classification (with granularity for LOOKUP), entity extraction (document_type, article_number, clause_number, point_label, so_ky_hieu, topic, time_reference), multi-intent decomposition, and confidence scoring.

#### Scenario: Analyze simple query
- **WHEN** user asks "Điều 17 Luật Doanh nghiệp 2020 quy định gì?"
- **THEN** output includes domain="QA", intent="LOOKUP", granularity="article", article_number=17, so_ky_hieu="LT-068-2020"

#### Scenario: Analyze complex multi-intent query
- **WHEN** user asks "Điều 17 Luật DN 2020 còn hiệu lực không, và khác gì Luật 2014?"
- **THEN** output includes 3 intents: LOOKUP, VALIDITY, COMPARISON with 3 sub-queries

#### Scenario: Analyze contract review query
- **WHEN** user says "Review hợp đồng này" with uploaded file
- **THEN** output includes domain="CONTRACT_REVIEW"

### Requirement: Prompt template management
The system SHALL manage LLM prompt templates for each analysis type (intent analysis, clause extraction, compliance analysis, answer generation). Templates SHALL be configurable and support variable substitution.

#### Scenario: Use intent analysis template
- **WHEN** analyzing a user query
- **THEN** system uses the intent analysis prompt template with user input substituted

#### Scenario: Update template without code change
- **WHEN** intent analysis prompt template is updated
- **THEN** system uses the new template without code deployment
