## Context

T5.1 intent analysis already exists and can return domains, intents, and `SubQuery` objects. Phase 4 also introduced a stronger retrieval direction using legal segments across Article, Clause, and Point nodes, hybrid search, graph context, and UID-based citation verification. Phase 5 should connect these pieces into a QA-first backend pipeline instead of creating another independent retrieval stack.

The current relationship and effective-text data is incomplete. `MODIFIES`, `SUPERSEDES`, and `EffectiveArticle` coverage cannot yet support definitive validity answers for all provisions. Validity must therefore be exposed as an explicit confidence signal rather than a hard legal conclusion.

## Goals / Non-Goals

**Goals:**

- Implement pure legal QA before contract-result QA, comparison-heavy QA, or frontend delivery.
- Consume `IntentClassification` and `SubQuery` output from T5.1.
- Reuse the Phase 4 legal segment retrieval core for topic, search, scenario, checklist, and numeric questions.
- Preserve direct lookup for explicit Article/Clause/Point references.
- Return strict JSON suitable for backend processing.
- Verify answer citations with graph UIDs first and text parsing as fallback.
- Represent validity as `verified`, `likely_current`, or `unknown` with a reason.

**Non-Goals:**

- Complete T3 effective-text composition.
- Guarantee definitive validity for provisions with incomplete relationship data.
- Build or change frontend UI behavior.
- Implement full comparison workflows beyond minimal scaffolding.
- Add new external dependencies.

## Decisions

### Wrap Phase 4 retrieval for QA

The QA retrieval layer will call the existing Phase 4 retrieval core for natural-language topic queries. It will normalize results into QA-specific provision objects rather than duplicating hybrid vector/full-text/graph logic.

Alternative considered: continue improving `src/llm/retriever.py` as an independent Article-only retrieval engine. This would duplicate ranking and graph context work and would not match the current graph where Clause and Point embeddings are important.

### Keep direct lookup separate from hybrid retrieval

Explicit references such as `Điều 17 Luật Doanh nghiệp 2020` need deterministic lookup. The pipeline will parse article, clause, point, document title, year, and `so_ky_hieu` hints when available, then fetch the matching graph path directly.

Alternative considered: send explicit references through hybrid search. This is less reliable because a precise citation should resolve by identity, not by similarity.

### Generate backend-first JSON answers

Answer generation will produce a strict JSON object containing the answer text, citations, retrieved provisions, intent metadata, and validity metadata. Human rendering can be built later from the JSON.

Alternative considered: stream natural-language tokens first and attach metadata later. That is useful for frontend responsiveness, but the current implementation need is backend processing and verification.

### Treat validity as best-effort

The QA output will never imply definitive validity unless graph evidence supports it. If `EffectiveArticle`, `is_current`, or relationship signals are missing, the response will mark validity as `unknown` or `likely_current` with an explanation.

Alternative considered: infer currentness from partial metadata or LLM judgment. That would create overconfident legal answers from incomplete graph data.

### Verify citations by UID first

Answer generation must preserve citation UIDs from retrieved provisions. Verification will resolve those UIDs in Neo4j and compare article/clause/point/document metadata when present. Citation text parsing remains a fallback for legacy or malformed outputs.

Alternative considered: parse display citations only. Vietnamese legal citations often omit document numbers or use short titles, so display-text-only verification is fragile.

## Risks / Trade-offs

- Incomplete graph relationships can weaken validity answers -> return explicit validity status and reason instead of definitive claims.
- LLM may emit malformed JSON -> enforce parsing, retry once where practical, and surface structured error metadata.
- Hybrid retrieval can return relevant but overbroad provisions -> include scores, source strategy, and retrieved provision metadata in the JSON for downstream filtering.
- Direct lookup depends on document resolution quality -> keep unresolved-reference status distinct from "no law exists".
- Reusing contract retrieval types may leak contract-specific naming -> introduce QA adapter objects while keeping the retrieval core shared.

## Migration Plan

1. Add QA response and provision data models.
2. Implement a QA retrieval adapter over direct lookup and Phase 4 hybrid retrieval.
3. Implement answer generation using the existing `answer_generation` prompt template.
4. Normalize generated citations into `LegalCitation` objects and verify them.
5. Add tests for lookup, topic QA, malformed JSON, UID verification, and best-effort validity.
6. Mark Phase 5 tasks complete only after the JSON pipeline runs end-to-end with mock services and can use Neo4j-backed retrieval when configured.

Rollback strategy: keep the existing T5.1 intent analyzer and Phase 4 retrieval code unchanged. If QA orchestration fails, callers can disable the new QA pipeline without affecting contract review.
