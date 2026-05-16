## 1. QA Data Contracts

- [x] 1.1 Define QA response, retrieved provision, validity, and citation verification dataclasses or typed dictionaries.
- [x] 1.2 Add serialization helpers so QA pipeline outputs JSON-compatible dictionaries.
- [x] 1.3 Extend or adapt existing `SubQuery` handling for QA-first strategy mapping without changing T5.1 public behavior.
- [x] 1.4 Add validation for generated answer JSON fields and citation UID membership.

## 2. QA Retrieval Adapter

- [x] 2.1 Implement a QA retrieval service that consumes `IntentClassification` and `SubQuery` objects.
- [x] 2.2 Implement deterministic direct lookup for Article, Clause, and Point references when document hints are available.
- [x] 2.3 Wrap Phase 4 `LegalHybridRetriever` for topic, search, scenario, checklist, and numeric QA queries.
- [x] 2.4 Normalize Phase 4 retrieval candidates into QA retrieved provision objects.
- [x] 2.5 Add best-effort validity metadata with `verified`, `likely_current`, and `unknown` statuses.
- [x] 2.6 Ensure missing graph relationships or EffectiveArticle nodes produce fallback metadata, not pipeline failure.

## 3. Answer Generation

- [x] 3.1 Implement a QA answer generation service using the existing `answer_generation` prompt template.
- [x] 3.2 Format retrieved provisions, effective text fallback, amendment context, and validity notes for the prompt.
- [x] 3.3 Parse LLM output as strict JSON and retry once on malformed JSON where practical.
- [x] 3.4 Return structured no-result answers when retrieval finds no provisions.
- [x] 3.5 Ensure answer citations reference retrieved provision UIDs.

## 4. Citation Verification

- [x] 4.1 Adapt `CitationVerifier` for QA answer citation objects.
- [x] 4.2 Verify citations by UID first and use citation text parsing only as fallback.
- [x] 4.3 Attach per-citation verification results to the QA JSON response.
- [x] 4.4 Add aggregate `citations_verified` status to the QA JSON response.
- [x] 4.5 Preserve validity uncertainty separately from citation existence verification.

## 5. QA Pipeline Orchestration

- [x] 5.1 Implement an end-to-end QA pipeline service: intent analysis → retrieval → answer generation → citation verification.
- [x] 5.2 Integrate optional `ConversationManager` context for follow-up QA without requiring persistent storage.
- [x] 5.3 Add explicit handling for unsupported domains such as CONTRACT_QA in the initial pure-QA pipeline.
- [x] 5.4 Expose a simple library entrypoint that backend routes can call later.
- [x] 5.5 Keep API/frontend changes out of this implementation unless a later change requests them.

## 6. Tests and Fixtures

- [x] 6.1 Add unit tests for intent-to-subquery QA strategy mapping.
- [x] 6.2 Add unit tests for direct lookup parsing and unresolved document references.
- [x] 6.3 Add unit tests for topic QA retrieval using mocked Phase 4 retriever results.
- [x] 6.4 Add unit tests for answer JSON parsing, malformed JSON retry behavior, and no-result answers.
- [x] 6.5 Add unit tests for UID-first citation verification and metadata mismatch handling.
- [x] 6.6 Add an end-to-end smoke test using mock LLM, mock retrieval, and mock citation verification.

## 7. OpenSpec Integration

- [x] 7.1 Update `openspec/changes/vietnamese-legal-knowledge-graph/tasks.md` T5.2, T5.3, and T5.4 status after implementation is complete.
- [x] 7.2 Run OpenSpec status/validation for this change before applying or archiving.
- [x] 7.3 Document known validity limitations in implementation notes or test fixtures.
