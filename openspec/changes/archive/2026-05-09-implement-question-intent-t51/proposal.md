## Why

Task T5.1 (Question Intent Analysis) is the entry point for the Legal QA Pipeline and the unified LLM Gateway. The current spec defines only 4 intent types (article_reference, topic, validity, comparison) which is insufficient for real user queries. Users ask about clauses, points, chapters, checklists, numeric thresholds, scenarios, and mix multiple intents in one question. Additionally, the system must handle both QA and Contract Review domains seamlessly, with conversation context for follow-up questions.

## What Changes

- Expand intent taxonomy from 4 to 10+ types with hierarchical model (Domain → Intent → Granularity)
- Add multi-intent decomposition into sub-queries for parallel processing
- Add domain classification (QA vs CONTRACT_REVIEW vs CONTRACT_QA vs EXPLAIN)
- Add so_ky_hieu resolution in T5.1 (using lookup table from T0.1)
- Add confidence threshold + fallback handling for unknown/ambiguous queries
- Add conversation context tracking for follow-up questions
- Unified LLM Gateway serving both Contract Review and QA pipelines

## Capabilities

### New Capabilities
- `question-intent-analysis`: Hierarchical intent classification with multi-intent decomposition, domain detection, entity extraction, and so_ky_hieu resolution for Vietnamese legal queries
- `unified-llm-gateway`: Single LLM layer serving both Contract Review and Legal QA pipelines with conversation state management

### Modified Capabilities
- `contract-review-pipeline`: T5.1-T5.4 specs updated to use unified LLM gateway and expanded intent taxonomy

## Impact

- `src/llm/` — new unified LLM module (client, intent analyzer, prompt templates)
- `src/contract/` — T4.2-T4.6 updated to use unified LLM client
- `openspec/specs/contract-review-pipeline/spec.md` — T5.1 spec update
- Dependencies: OpenAI SDK (configurable model + API key)
- Conversation state storage (in-memory for MVP)
