## Context

T5.1 (Question Intent Analysis) is the entry point for the Legal QA Pipeline. The original spec defines only 4 intent types, which is insufficient for real user queries. After exploration, we identified 10+ intent types across 5 domains, with multi-intent decomposition and conversation context tracking.

T4.1 (Contract Parser) is complete. T5.1 can proceed independently — no dependency on B's graph work.

## Goals / Non-Goals

**Goals:**
- Hierarchical intent classification: Domain → Intent → Granularity
- Multi-intent decomposition into sub-queries for parallel processing
- so_ky_hieu resolution using lookup table from T0.1
- Confidence threshold + fallback for unknown/ambiguous queries
- Conversation context tracking for follow-up questions
- Unified LLM client with configurable provider + mock for dev

**Non-Goals:**
- T5.2 (Retrieval) — intent analysis only, no graph queries
- T5.3 (Answer Generation) — intent analysis only, no LLM answer generation
- Web UI — CLI/library only
- Persistent conversation storage — in-memory for MVP

## Decisions

### 1. Hierarchical Intent Model

**Decision**: 3-level hierarchy: Domain → Intent → Granularity

**Rationale**:
- Domain level separates QA from Contract Review from EXPLAIN
- Intent level captures the specific question type
- Granularity level handles article/clause/point/document distinctions

**Alternatives considered**:
- Flat list of 15+ intents: Too hard to maintain, no structure
- Two-level (Domain + Intent): Missing granularity for LOOKUP queries

### 2. Multi-Intent Decomposition

**Decision**: Decompose complex queries into sub-queries with retrieval strategies

**Rationale**:
- Each sub-query can be processed in parallel by T5.2
- User sees system understood all parts of their question
- Easy to debug and test

**Alternatives considered**:
- Single primary + secondary intents: Loses detail for retrieval
- Process all intents together: Hard to parallelize

### 3. so_ky_hieu Resolution in T5.1

**Decision**: Resolve so_ky_hieu using lookup table from T0.1

**Rationale**:
- T5.2 needs doc_id for direct lookup — cannot delay resolution
- Lookup table already exists (output/so_ky_hieu_lookup.json)
- Fuzzy match fallback for non-standard formats

### 4. Unified LLM Client

**Decision**: Single LLMClient abstract class with configurable providers

**Rationale**:
- Both Contract Review and QA use LLM — avoid duplication
- Easy to switch providers (OpenAI, Claude, local)
- Mock provider for development/testing

### 5. Confidence Threshold + Fallback

**Decision**: 3-tier confidence handling (proceed, clarify, fallback)

**Rationale**:
- High confidence (>=0.7): Proceed normally
- Medium (0.4-0.7): Ask clarification — better than wrong answer
- Low (<0.4): Fallback to general response

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| LLM API cost | Mock provider for dev, batch requests in production |
| LLM latency | Cache common intent patterns, async processing |
| Vietnamese understanding | Test with real Vietnamese legal queries, iterate prompts |
| Conversation context growth | Limit context window, expire old conversations |
| so_ky_hieu lookup misses | Fuzzy match + ask user for clarification |

## T5.2 Retrieval Strategies

T5.1 outputs `sub_queries` with `retrieval_strategy` field. T5.2 executes the appropriate Cypher query based on strategy.

### Strategy Mapping

| Intent | Strategy | Data Sources | Mockable? |
|--------|----------|--------------|-----------|
| LOOKUP (article) | `direct_lookup` | Article.uid → direct MATCH + EffectiveArticle | ✅ Yes |
| LOOKUP (clause) | `clause_lookup` | Article → HAS_CLAUSE → Clause uid | ✅ Yes |
| LOOKUP (point) | `point_lookup` | Clause → HAS_POINT → Point uid | ✅ Yes |
| VALIDITY (document) | `validity_check` | Document.tinh_trang_hieu_luc + Article.is_current | ✅ Yes |
| VALIDITY (article) | `article_validity` | EffectiveArticle.is_current + amendment_chain | ✅ Yes |
| COMPARISON | `comparison` | Parallel direct_lookup × N + diff effective_text | ✅ Yes |
| TOPIC | `topic_search` | Vector search + graph traversal + EffectiveArticle | ❌ Needs T1.6 |
| CHECKLIST | `checklist_search` | Fulltext search + filter loai_van_ban + nganh | ✅ Yes |
| NUMERIC | `numeric_search` | Vector search + regex extract numbers | ❌ Needs T1.6 |
| SCENARIO | `scenario_search` | Vector search + graph traversal + MODIFIES | ❌ Needs T2.x |
| SEARCH | `aggregate_search` | Fulltext + vector + aggregation | ❌ Needs T1.6 |
| CONTRACT_QA | `lookup_violation` | Contract → ContractClause → GOVERNED_BY → EffectiveArticle | ❌ Needs T4.2 |

### direct_lookup Cypher

```cypher
// Case: Lookup specific article with effective text
MATCH (d:Document {so_ky_hieu: $so_ky_hieu})
<-[:HAS_ARTICLE]-(a:Article {index: $article_number})
OPTIONAL MATCH (ea:EffectiveArticle)-[:COMPOSED_FROM]->(a)
WHERE ea.is_current = true
RETURN a.uid, a.index, a.title, a.clean_text,
       a.is_current, a.effective_date,
       ea.effective_text AS current_text,
       ea.as_of_date, ea.amendment_chain
```

### validity_check Cypher

```cypher
// Document validity
MATCH (d:Document {so_ky_hieu: $so_ky_hieu})
RETURN d.so_ky_hieu, d.title,
       d.tinh_trang_hieu_luc,
       d.ngay_co_hieu_luc, d.ngay_het_hieu_luc,
       EXISTS { (d)-[:SUPERSEDED_BY]->(:Document) } AS is_superseded,
       [(d)-[:SUPERSEDED_BY]->(s) | {
         so_ky_hieu: s.so_ky_hieu, title: s.title
       }] AS superseded_by
```

### comparison Cypher

```cypher
// Parallel retrieval for each document
UNWIND $documents AS doc_info
MATCH (d:Document {so_ky_hieu: doc_info.so_ky_hieu})
OPTIONAL MATCH (d)<-[:HAS_ARTICLE]-(a:Article {index: $article_number})
OPTIONAL MATCH (ea:EffectiveArticle)-[:COMPOSED_FROM]->(a)
WHERE ea.is_current = true
RETURN d.so_ky_hieu, d.title, d.ngay_ban_hanh,
       a.uid, a.clean_text, ea.effective_text, ea.amendment_chain
```

### topic_search Cypher

```cypher
// Vector search + graph traversal
CALL db.index.vector.queryNodes('article_embeddings', 20, $topic_embedding)
YIELD node AS article, score
WHERE article.is_current = true
MATCH (article)<-[:HAS_ARTICLE]-(d:Document)
WHERE d.tinh_trang_hieu_luc = 'con_hieu_luc'
OPTIONAL MATCH (ea:EffectiveArticle)-[:COMPOSED_FROM]->(article)
WHERE ea.is_current = true
RETURN article.uid, article.clean_text, ea.effective_text,
       d.so_ky_hieu, d.title, d.loai_van_ban, score
ORDER BY score DESC LIMIT 5
```

### lookup_violation Cypher (CONTRACT_QA)

```cypher
// Get contract clause + governing legal provisions
MATCH (c:Contract {id: $contract_id})-[:HAS_CLAUSE]->(cc:ContractClause {index: $clause_index})
OPTIONAL MATCH (cc)-[:GOVERNED_BY]->(ea:EffectiveArticle)
OPTIONAL MATCH (ea)-[:COMPOSED_FROM]->(a:Article)
OPTIONAL MATCH (a)<-[:HAS_ARTICLE]-(d:Document)
RETURN cc.text_content, cc.clause_type,
       ea.effective_text, ea.amendment_chain,
       a.uid, d.so_ky_hieu, d.title
```
