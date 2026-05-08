# Spec: Contract Review Pipeline

## Overview

Build an end-to-end pipeline that takes a contract (PDF, Word, or plain text), extracts clauses, matches them against legal provisions in the Neo4j knowledge graph, and generates a compliance analysis report with precise citations.

## Capabilities

### Parse contracts

Extract raw text from contract documents in multiple formats.

- **PDF**: Use PyMuPDF (fitz) for text-based PDFs. Extract text page by page, preserving page numbers for citation.
- **PDF (scanned)**: Detect scanned PDFs (text extraction yields <50 characters per page). Fall back to Tesseract OCR with Vietnamese language pack (vie). Use PyMuPDF for image extraction, Tesseract for OCR.
- **Word (.docx)**: Use python-docx for text extraction. Preserve paragraph structure. Handle tables (convert to structured text).
- **Plain text**: Direct use, no processing needed.
- For all formats: clean whitespace, normalize Vietnamese diacritics, remove page headers/footers if detectable.
- Output: Contract node with raw_text, source_format, upload_date

### Extract contract clauses

Use LLM to identify and structure individual clauses from contract text.

- LLM prompt extracts: clause index, clause_type (thanh_toán, bảo_hành, phạt, chấm_dứt, bồi_thường, bảo_mật, giải_quyết_tranh_chấp, force_majeure, etc.), text_content, parties involved, obligations described
- Output: list of ContractClause nodes linked to Contract
- For each ContractClause, generate embedding using vietlegal-harrier-0.6b
- Target: ≥90% clause extraction accuracy on test contracts (measured by human evaluation)

### Match legal provisions

For each ContractClause, find the most relevant legal provisions using vector search + graph traversal.

- Step A: Semantic search
  - Embed ContractClause.text_content using vietlegal-harrier-0.6b
  - Vector similarity search in Neo4j (cosine similarity) against Article.embeddings
  - Retrieve top-20 most similar Articles
  - Filter: is_current=true, loai_van_ban priority (Luật > ND > TT > TTLT)
  - Filter: nganh/linh_vuc relevance to contract type

- Step B: Graph traversal (Neo4j Cypher)
  - From each matched Article, traverse:
    - [:REFERENCES_INTERNAL] → related Articles within same Document (expand context)
    - [:REFERENCES_EXTERNAL] → related Articles in other Documents (cross-references)
    - [:MODIFIES] ← incoming amendments → get EffectiveArticle (current text)
    - ← [:HAS_ARTICLE] ← Document → [:DETAILS] ← implementing ND/TT (find specific regulations)
  - Collect full context: original Article text + all referenced provisions + effective text

- Step C: Reranking
  - Combine semantic score × authority weight
  - Authority weight: Luật (3.0) > ND (2.0) > TT (1.5) > TTLT (1.0)
  - Boost Articles found via graph traversal (cross-reference discovered) by 1.5×
  - Return top-5 legal provisions per contract clause

### Analyze compliance

Generate structured compliance report using LLM with legal provisions as context.

- LLM input per contract clause:
  - Contract clause text
  - Matched legal provisions (EffectiveArticle text)
  - Amendment history (which documents modified this provision)
  - Parent Document metadata (validity, scope, issuing authority)
  - Detailing ND/TT (if available via [:DETAILS] relationship)

- LLM output per clause:
  - **Vi phạm pháp luật** (legal violations): specific provisions that the contract clause contradicts
  - **Rủi ro pháp lý** (legal risks): provisions that create risk if the clause is unclear or silent
  - **Đề xuất sửa đổi** (suggested revisions): specific text changes to ensure compliance
  - **Trích dẫn nguồn** (citations): precise Điều X khoản Y Luật/ND/TT format

- Each citation must include: document so_ky_hieu, Điều number, Khoản/Điểm if applicable, document title, effective date

### Verify citations

Automated verification that every citation in LLM output resolves to an existing node in Neo4j.

- Parse citation format: "Điều {N} khoản {K} {Loại_văn_bản} {so_ky_hieu}"
- Lookup in Neo4j: MATCH (a:Article {index: N})<-[:HAS_ARTICLE]-(d:Document {so_ky_hieu: normalized_skh})
- Verify: Article exists, Document exists, Clause/Khoản exists (if specified), is_current=true
- For each citation: mark as VERIFIED or UNVERIFIED with reason
- UNVERIFIED citations flagged for human review
- Target: 100% of citations verified (verified or explicitly flagged)

### Review policies

Extension of contract review for internal policy compliance checking.

- Same pipeline as contract clause matching and compliance analysis
- Additional analysis: flag where policy provisions are more restrictive than law (compliant but potentially costly)
- Classification: "compliant_and_efficient" (meets law, no excess), "compliant_but_restrictive" (exceeds legal requirements), "non_compliant" (violates law)
- Output: policy compliance report with same citation format