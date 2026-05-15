## ADDED Requirements

### Requirement: SubQuery consumption by retrieval pipeline
The retrieval pipeline (T5.2) SHALL consume SubQuery objects produced by intent analysis (T5.1). Each SubQuery contains: intent (intent type), query (natural language text), retrieval_strategy (strategy name: direct_lookup, vector_search, validity_check, comparison, etc.), and requires (list of data sources needed: contract_context, legal_provision, effective_text). The retrieval engine SHALL route each SubQuery to the appropriate strategy based on retrieval_strategy.

#### Scenario: Route direct lookup sub-query
- **WHEN** SubQuery has retrieval_strategy="direct_lookup"
- **THEN** retrieval engine executes direct lookup strategy

#### Scenario: Route vector search sub-query
- **WHEN** SubQuery has retrieval_strategy="vector_search"
- **THEN** retrieval engine executes vector search strategy

#### Scenario: Handle multiple sub-queries
- **WHEN** intent analysis produces 3 sub-queries for a complex question
- **THEN** retrieval engine processes each sub-query with its respective strategy
