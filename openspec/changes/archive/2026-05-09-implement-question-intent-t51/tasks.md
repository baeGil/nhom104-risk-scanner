## 1. Setup

- [x] 1.1 Create `src/llm/` module structure (`__init__.py`, `client.py`, `intent.py`, `prompts.py`, `models.py`)
- [x] 1.2 Add `openai` and `pydantic` to project dependencies
- [x] 1.3 Create `.env.example` with LLM_API_KEY and LLM_MODEL placeholders

## 2. LLM Models

- [x] 2.1 Define `IntentClassification` dataclass (domain, confidence, intents[], sub_queries[])
- [x] 2.2 Define `SubIntent` dataclass (type, confidence, query_span, extracted)
- [x] 2.3 Define `SubQuery` dataclass (intent, query, retrieval_strategy, requires)
- [x] 2.4 Define `ConversationContext` dataclass (conversation_id, turn_number, history, referenced_contracts)

## 3. Unified LLM Client

- [x] 3.1 Create `LLMClient` abstract base class with chat(), extract(), classify() methods
- [x] 3.2 Implement `OpenAIClient` provider (configurable model via env)
- [x] 3.3 Implement `MockLLMClient` provider for development/testing — REMOVED (no mock/hardcode)
- [x] 3.4 Implement provider factory (load from config/env)
- [x] 3.5 Implement JSON response parsing with markdown code block stripping

## 4. Prompt Templates

- [x] 4.1 Create intent analysis prompt template (Vietnamese legal domain)
- [x] 4.2 Create clause extraction prompt template (for T4.2)
- [x] 4.3 Create compliance analysis prompt template (for T4.4)
- [x] 4.4 Create answer generation prompt template (for T5.3)
- [x] 4.5 Implement template variable substitution system

## 5. Intent Analyzer (T5.1 Core)

- [x] 5.1 Implement `IntentAnalyzer` class with `analyze(query, context)` method
- [x] 5.2 Implement domain classification (QA, CONTRACT_REVIEW, CONTRACT_QA, EXPLAIN, CHITCHAT)
- [x] 5.3 Implement intent classification with granularity (LOOKUP: chapter/article/clause/point/document)
- [x] 5.4 Implement entity extraction (document_type, article_number, clause_number, point_label, so_ky_hieu)
- [x] 5.5 Implement multi-intent decomposition into sub-queries
- [x] 5.6 Implement so_ky_hieu resolution using lookup table from T0.1 — deferred (depends on T0.1)
- [x] 5.7 Implement confidence threshold handling (proceed, clarify, fallback)

## 6. Conversation Context

- [x] 6.1 Implement `ConversationManager` with in-memory storage
- [x] 6.2 Implement context tracking (turn_number, previous intents, referenced contracts)
- [x] 6.3 Implement follow-up reference resolution ("điều khoản đó" → previous clause)
- [x] 6.4 Implement context expiration (max turns, TTL)

## 7. Tests

- [x] 7.1 Create `src/llm/tests/` directory with test structure
- [x] 7.2 Write unit tests for OpenAIClient
- [x] 7.3 Write unit tests for intent classification (all 8 intent types)
- [x] 7.4 Write unit tests for multi-intent decomposition
- [x] 7.5 Write unit tests for so_ky_hieu resolution — deferred (depends on T0.1)
- [x] 7.6 Write unit tests for confidence threshold handling
- [x] 7.7 Write integration tests for IntentAnalyzer with OpenAIClient
- [x] 7.8 Write tests for conversation context tracking
