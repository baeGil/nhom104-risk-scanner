# Vietnamese Legal Knowledge Graph — Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE                            │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Phase 0  │──▶│ Phase 1  │──▶│ Phase 2  │──▶│ Phase 3  │    │
│  │ Clean &  │   │ Segment │   │   XRef   │   │ Compose │    │
│  │ Normalize│   │ (Parse) │   │ Extract  │   │ Effective│    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│       │              │              │              │              │
│       ▼              ▼              ▼              ▼              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Neo4j Knowledge Graph                  │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │    │
│  │  │Document │  │Article  │  │Effective│  │Contract │    │    │
│  │  │  Nodes  │  │  Nodes  │  │ Article │  │  Nodes  │    │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│       │              │              │              │              │
│       ▼              ▼              ▼              ▼              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    APPLICATION LAYER                     │    │
│  │  ┌──────────────┐          ┌──────────────┐              │    │
│  │  │ Legal QA Bot │          │  Contract    │              │    │
│  │  │              │          │  Reviewer    │              │    │
│  │  └──────────────┘          └──────────────┘              │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Neo4j Graph Model

### Node Types

```cypher
(:Document {
  id: INT,
  so_ky_hieu: STRING,         -- normalized, e.g., "ND-046-2014"
  so_ky_hieu_raw: STRING,     -- original from metadata
  title: STRING,
  loai_van_ban: STRING,       -- "Luật" | "Nghị định" | "Thông tư" | "Thông tư liên tịch"
  ngay_ban_hanh: DATE,
  ngay_co_hieu_luc: DATE,
  ngay_het_hieu_luc: DATE,    -- nullable
  tinh_trang_hieu_luc: STRING,
  co_quan_ban_hanh: STRING,
  nganh: STRING,
  linh_vuc: STRING,
  pham_vi: STRING,
  content_hash: STRING         -- SHA256 of clean_html for change detection
})

(:Chapter {
  index: INT,
  roman: STRING,               -- "I", "II", "III"...
  title: STRING
})

(:Article {
  uid: STRING,                 -- "doc_{id}_dieu_{index}"
  index: INT,                  -- article number
  title: STRING,               -- e.g., "Phạm vi điều chỉnh"
  text_content: STRING,        -- full text of this Điều (all clauses)
  clean_text: STRING,          -- stripped HTML
  embedding: FLOAT[],          -- vector embedding
  is_current: BOOLEAN,         -- still effective?
  effective_date: DATE         -- most recent amendment effective date
})

(:Clause {
  uid: STRING,                 -- "doc_{id}_dieu_{dieu_idx}_khoan_{idx}"
  index: INT,                  -- clause number (1, 2, 3...)
  text_content: STRING,
  clean_text: STRING
})

(:Point {
  uid: STRING,                 -- "doc_{id}_dieu_{dieu_idx}_khoan_{khoan_idx}_diem_{letter}"
  letter: STRING,              -- "a", "b", "c"...
  text_content: STRING,
  clean_text: STRING
})

(:EffectiveArticle {
  uid: STRING,                 -- "eff_{article_uid}_{date}"
  as_of_date: DATE,
  effective_text: STRING,      -- composed text (original + all amendments merged)
  amendment_chain: STRING[],   -- ordered list of modifying Article uids
  is_current: BOOLEAN,
  changes_count: INT            -- number of amendments applied
})

(:Contract {
  id: STRING,                  -- UUID
  raw_text: STRING,
  upload_date: DATE,
  contract_type: STRING,       -- "mua_ban" | "dich_vu" | "lao_dong" | etc.
  source_format: STRING        -- "pdf" | "docx" | "txt"
})

(:ContractClause {
  id: STRING,                  -- UUID
  index: INT,
  clause_type: STRING,          -- "thanh_toan" | "bao_hanh" | "phat" | etc.
  text_content: STRING,
  embedding: FLOAT[]
})
```

### Relationship Types

```cypher
-- Hierarchy
(:Document)-[:HAS_CHAPTER {order: INT}]->(:Chapter)
(:Chapter)-[:HAS_ARTICLE {order: INT}]->(:Article)
(:Document)-[:HAS_ARTICLE {order: INT}]->(:Article)
(:Article)-[:HAS_CLAUSE {order: INT}]->(:Clause)
(:Clause)-[:HAS_POINT {order: INT}]->(:Point)
(:Article)-[:HAS_POINT {order: INT}]->(:Point)

-- Document-level relationships (from existing metadata)
(:Document)-[:CITES]->(:Document)
(:Document)-[:REFERRED_BY]->(:Document)
(:Document)-[:DETAILS]->(:Document)
(:Document)-[:DETAILED_BY]->(:Document)
(:Document)-[:SUPERSEDES]->(:Document)
(:Document)-[:SUPERSEDED_BY]->(:Document)
(:Document)-[:PARTIALLY_SUPERSEDES]->(:Document)
(:Document)-[:AMENDS]->(:Document)
(:Document)-[:AMENDED_BY]->(:Document)
(:Document)-[:SUPPLEMENTS]->(:Document)
(:Document)-[:SUPPLEMENTED_BY]->(:Document)

-- Article-level cross-references
(:Article)-[:REFERENCES_INTERNAL {
  context: STRING
}]->(:Article)

(:Article)-[:REFERENCES_EXTERNAL {
  context: STRING,
  target_so_ky_hieu: STRING
}]->(:Article)

(:Article)-[:MODIFIES {
  action: STRING,              -- "sửa đổi" | "bổ sung" | "thay thế" | "bãi bỏ"
  target_clause: INT,
  target_point: STRING,
  context: STRING
}]->(:Article)

-- Validity
(:EffectiveArticle)-[:COMPOSED_FROM]->(:Article)
(:EffectiveArticle)-[:AMENDED_BY {order: INT}]->(:Article)

-- Contract review
(:Contract)-[:HAS_CLAUSE]->(:ContractClause)
(:ContractClause)-[:GOVERNED_BY]->(:Article)
(:ContractClause)-[:GOVERNED_BY]->(:EffectiveArticle)
(:ContractClause)-[:REFERENCES]->(:Article)
```

### Indexes

```cypher
CREATE INDEX doc_so_ky_hieu IF NOT EXISTS FOR (d:Document) ON (d.so_ky_hieu);
CREATE INDEX doc_loai IF NOT EXISTS FOR (d:Document) ON (d.loai_van_ban);
CREATE INDEX doc_hieu_luc IF NOT EXISTS FOR (d:Document) ON (d.tinh_trang_hieu_luc);
CREATE INDEX article_uid IF NOT EXISTS FOR (a:Article) ON (a.uid);
CREATE INDEX article_current IF NOT EXISTS FOR (a:Article) ON (a.is_current);
CREATE INDEX clause_uid IF NOT EXISTS FOR (c:Clause) ON (c.uid);

CREATE FULLTEXT INDEX doc_search IF NOT EXISTS FOR (d:Document) ON EACH [d.title, d.so_ky_hieu];
CREATE FULLTEXT INDEX article_search IF NOT EXISTS FOR (a:Article) ON EACH [a.title, a.clean_text);

CREATE VECTOR INDEX article_embeddings IF NOT EXISTS
FOR (a:Article) ON (a.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 768,
  `vector.similarity_function`: 'cosine'
}};
```

## Data Pipeline

### Phase 0: Data Clean & Normalize

**so_ky_hieu Normalization:**

Parse raw so_ky_hieu into structured components and generate a normalized form suitable for lookup and cross-reference resolution.

```
Raw inputs:
  "46/2014/NĐ-CP"  → {type: "Nghị định", number: 46, year: 2014, issuer: "CP", normalized: "ND-046-2014"}
  "68/2014/QH13"   → {type: "Luật", number: 68, year: 2014, session: "QH13", normalized: "LT-068-2014"}
  "25/2017/TT-BTC"  → {type: "Thông tư", number: 25, year: 2017, issuer: "BTC", normalized: "TT-025-2017-BTC"}
  "79-TP/NĐ"        → {type: "Nghị định", number: 79, year: null, issuer: "TP", normalized: "ND-079-????-TP"}
  "Không số"        → {type: unknown, skip normalization}

Resolution priority:
  1. Exact match on normalized so_ky_hieu + loai_van_ban + year
  2. Fuzzy match (Levenshtein distance ≤ 2) on so_ky_hieu
  3. Year + loai_van_ban + title substring match
  4. Flag for manual resolution
```

**Content Cleaning:**

Strip wrapper `<table class="detailcontent">`, remove `<font>` tags (keep content, drop formatting), normalize `<p>` tags (remove empty ones), preserve `<b>` and `<strong>` (essential for hierarchy detection), preserve `<i>` and `<em>` (definitions, references), remove `<dir>` tags. Store both raw_html and clean_html.

**Deduplication:**

Same so_ky_hieu + same loai_van_ban + same year → same document. Keep version with most content, merge metadata (prefer non-null fields). 1,273 exact duplicates identified.

**Missing Content Crawl:**

For 2,637 core documents missing from content.parquet, crawl from thuvienphapluat.vn. Extract HTML content from detail page using so_ky_hieu as search key. Insert into content.parquet with matching doc_id. Preserve all metadata fields unchanged. Target: ≥95% content coverage for effective core docs.

### Phase 1: Segment — Parse Hierarchy

**Rule-based Parser (80-85% coverage):**

State machine processing cleaned HTML top-to-bottom:

```
State: {doc_id, current_chapter, current_article, current_clause, current_point}

Priority detection order:
1. Chương: /^Chương\s+[IVXL]+\s*\.?\s/i  → push chapter state
2. Điều:  /^[Đđ][ií]ều\s+\d+[\.:\s]/      → push article state
3. Khoản: /^\d+\.\s/ (contextual, after Điều) → push clause state
4. Điểm:  /^[a-z]\)\s/ (after Khoản)         → push point state
5. Điểm nhỏ: /^[ivx]+\)\s/ (rare)            → push point state

Context rules:
- Điều resets khoản counter
- Khoản resets điểm counter
- "Căn cứ..." preamble → skip (not a section)
- Table content → attach to parent clause/article
```

**Confidence Scoring:**

Each parsed document gets a confidence score. High (≥0.9): ≥80% of expected Điều found, clear formatting. Medium (0.6-0.9): some misalignment. Low (<0.6): poor structure, flag for LLM fallback.

### Phase 2: XRef — Extract Cross-References

**Internal references** — regex on Article/Clause/Point text for same-document references (Điều X, khoản Y, điểm Z). Create [:REFERENCES_INTERNAL] relationships.

**External references** — regex for cross-document references (Luật/ND/TT + so_ky_hieu). Resolve via lookup table from Phase 0. Fuzzy match fallback for non-standard formats. Create [:REFERENCES_EXTERNAL] relationships.

**Modification references** — for 3,092 modifying documents (identified from relationship data), parse each Điều to extract: action, target_doc, target_Điều, target_Khoản, target_Điểm. Create [:MODIFIES] relationships. Target: 5K-8K article-level modification links.

### Phase 3: Compose — Effective Text

**Amendment Chain Algorithm:**

For each Article with incoming [:MODIFIES] edges: collect and order modifications by modifying_doc.ngay_ban_hanh ASC. Apply transformations sequentially: "sửa đổi" (replace clause text), "bổ sung" (insert new point/point), "thay thế" (replace entire segment), "bãi bỏ" (mark as voided). Store composed effective_text on EffectiveArticle node.

**Validation:**

Compare composed result against 35 VB hợp nhất documents (ground truth). Automated check: does effective_text alignment match Document.tinh_trang_hieu_luc. Flag mismatches for manual review. Target: ≥90% agreement.

## Application Layer

### Contract Review Pipeline

1. **Contract Input** (PDF/Word/TXT) → Parser → Extract clauses → LLM extraction (clause_type, parties, obligations)

2. **Legal Provision Matching** (per clause):
   - Embed clause text using vietlegal-harrier-0.6b
   - Vector similarity search → top-20 Articles
   - Filter: is_current=true, loai_van_ban priority
   - Graph traversal: [:REFERENCES_INTERNAL], [:MODIFIES], [:DETAILS]
   - Get EffectiveArticle current text
   - Rerank by semantic score × graph authority

3. **Compliance Analysis** (LLM): contract clause + matched provisions + effective text + amendment history → violations, risks, suggestions, citations

4. **Citation Verification**: every citation verified against Neo4j graph

### Legal QA Pipeline

1. **Intent Analysis** (LLM): extract topic, document type, article reference, time reference
2. **Retrieval**: article reference → direct graph lookup; topic query → vector search + graph traversal
3. **Answer Generation** (LLM): question + retrieved provisions + effective text + amendment history
4. **Citation Verification**: same as contract review

## Embedding Strategy

**Model:** `mainguyen9/vietlegal-harrier-0.6b` — Vietnamese legal-domain specific, 768-dimensional vectors, self-hosted.

Embed at Article level (full text including all clauses). Clause/Point-level retrieval via graph traversal from matched Article. ContractClause embeddings for contract-to-law matching.

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Graph Database | Neo4j (self-hosted) |
| Embedding Model | mainguyen9/vietlegal-harrier-0.6b |
| Parsing | Python (BeautifulSoup + regex) |
| LLM (future) | GPT-4o-mini / Claude Haiku |
| Web Framework | Python (FastAPI) |
| Data Processing | Python (pandas, pyarrow) |
| Vector Search | Neo4j vector index |
| Contract Parsing | PyMuPDF + Tesseract OCR + python-docx |
| Crawler | requests + BeautifulSoup |

## Data Scale Estimates

| Metric | Value |
|--------|-------|
| Document nodes | ~14,265 (effective core) |
| Chapter nodes | ~5,000 |
| Article nodes | ~160,000 |
| Clause nodes | ~400,000 |
| Point nodes | ~300,000 |
| EffectiveArticle nodes | ~50,000 |
| Internal reference edges | ~100,000 |
| External reference edges | ~102,000 |
| Modification edges | ~5,000-8,000 |
| Document-level edges | ~659,000 |
| Total nodes | ~900K |
| Total edges | ~870K |