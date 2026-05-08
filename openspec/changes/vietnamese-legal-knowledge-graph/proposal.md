# Vietnamese Legal Knowledge Graph

## Problem

We are building a production-grade legal chatbot for Vietnamese law QA and contract/policy review. Our dataset contains 153,420 legal documents with metadata, 178,665 content records (HTML), and 897,890 document-level relationships. However, the current data only has **document-level** relationships — when a user or contract references "Điều 17 khoản 2 Luật Doanh nghiệp", we cannot retrieve the exact article, its amendments, or its current effective text.

This is the critical blocker: legal citations operate at the **Điều/Khoản/Điểm** level, not the document level. Without article-level granularity:

- We cannot compose effective text (original + amendments)
- We cannot verify whether a specific provision is still valid
- We cannot trace cross-references between provisions
- Contract review cannot match contract clauses to precise legal provisions

## Solution

Build a Neo4j knowledge graph that breaks documents into hierarchical segments (Chương → Điều → Khoản → Điểm), extracts article-level cross-references, composes amendment chains, and pre-computes effective text. This graph will power both a legal QA chatbot and a contract review system.

## Scope

**In scope:**
- Luật, Nghị định, Thông tư, Thông tư liên tịch (27,525 total, 14,265 effective)
- HTML parsing → hierarchical segments
- Article-level cross-reference extraction
- Amendment chain composition
- Effective text pre-computation
- Neo4j graph model with vector search
- Contract parser (PDF, Word, plain text)
- Contract review pipeline
- Legal QA pipeline

**Out of scope (future):**
- Other document types (Quyết định, Chỉ thị, Sắc lệnh, etc.)
- LLM-assisted parsing (Phase 2 — budget permitting)
- Real-time crawling of new documents
- Multi-turn conversational memory for QA
- Constitutional court interpretations (Nghị quyết ANTD)

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Graph database | Neo4j (self-hosted) | Rich traversal, vector search plugin, battle-tested for legal graphs |
| Embedding model | mainguyen9/vietlegal-harrier-0.6b | Vietnamese legal-domain specific, self-hosted, no API cost |
| Parsing strategy | Rule-first, LLM-later | Budget constraint; rules handle 80-85% of docs |
| Amendment composition | Rule-based pre-compute + validation | Pre-compute effective text; validate against 35 VB hợp nhất |
| Missing content | Crawl from thuvienphapluat.vn | Fill 2,637 document gaps, preserve existing metadata |
| so_ky_hieu resolution | Normalize + fuzzy match | 25-30% non-standard formats require normalization |

## Dataset Overview

| Metric | Value |
|--------|-------|
| Total core docs (Luật/ND/TT) | 27,525 |
| Effective core docs | 14,265 |
| With content | 12,921 |
| Missing content (to crawl) | 2,637 |
| Document-level relationships | 897,890 |
| Amendment relationships | 6,536 |
| Estimated segment nodes | ~900K |
| VB hợp nhất (ground truth) | 35 |

## Success Criteria

1. **Segmentation**: ≥80% of effective core docs parsed with High confidence
2. **Cross-reference resolution**: ≥95% of standard-format refs resolved
3. **Effective text**: ≥90% agreement with VB hợp nhất ground truth
4. **Contract review**: Top-5 legal provisions retrieved per clause with relevant citations
5. **QA accuracy**: Precise Điều/Khoản/Điểm citations verified against Neo4j graph