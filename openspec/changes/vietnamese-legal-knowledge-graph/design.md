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

### Contract Parser (T4.1) — Design Decision

**Decision**: Use [MinerU](https://github.com/opendatalab/MinerU) (Apache 2.0) instead of PyMuPDF + python-docx + Tesseract.

**Rationale**:
- Single library handles PDF, DOCX, TXT → Markdown
- Built-in OCR with Vietnamese support (109 languages)
- Auto-detects scanned vs text-based PDFs
- Auto-removes headers, footers, page numbers
- Preserves document structure (headings, tables as HTML)
- Apache 2.0 license (commercial-friendly)
- Active development (62k+ stars, v3.1.0)

**Pipeline**:
```
Input: PDF/DOCX/TXT
     ↓
┌──────────────────────────┐
│ MinerU                   │
│ → Markdown output        │
│ → Auto OCR (scanned)     │
│ → Remove header/footer   │
└──────────────────────────┘
     ↓
┌──────────────────────────┐
│ PII Detection/Redaction  │
│ - Regex patterns         │
│ - Vietnamese PII types   │
└──────────────────────────┘
     ↓
Output: Contract {
  id: UUID,
  raw_text: str,           # Markdown from MinerU
  redacted_text: str,      # PII redacted
  source_format: str,      # "pdf" | "docx" | "txt"
  upload_date: date,
  pii_map: dict            # PII value → placeholder mapping
}
```

**PII Types Detected** (Vietnamese contracts):
| Type | Pattern | Example |
|------|---------|---------|
| CCCD/CMND | 9-12 digits | `079087654321` |
| Mã số thuế | 10-13 digits | `0123456789` |
| Số điện thoại | +84/0 prefix | `0901234567` |
| Email | Standard email | `name@company.vn` |
| Số tài khoản | 10-16 digits (with context) | `1234567890123` |
| Địa chỉ | Vietnamese address keywords | `số 123 đường ABC, quận XYZ` |
| Họ tên | Context-based (after "Ông/Bà/Công ty") | `Nguyễn Văn A` |

**PII Redaction Strategy**:
- Replace with placeholders: `[REDACTED_CCCD]`, `[REDACTED_PHONE]`, etc.
- Keep `pii_map` for authorized access (reversible if needed)
- Store both `raw_text` (full) and `redacted_text` (safe for LLM processing)

### Contract Review Pipeline

1. **Contract Input** (PDF/Word/TXT) → MinerU Parser → PII Redaction → Extract clauses → LLM extraction (clause_type, parties, obligations)

2. **Legal Provision Matching** (per clause):
   - Embed clause text using vietlegal-harrier-0.6b
   - Vector similarity search → top-20 Articles
   - Filter: is_current=true, loai_van_ban priority
   - Graph traversal: [:REFERENCES_INTERNAL], [:MODIFIES], [:DETAILS]
   - Get EffectiveArticle current text
   - Rerank by semantic score × graph authority

3. **Compliance Analysis** (LLM): contract clause + matched provisions + effective text + amendment history → violations, risks, suggestions, citations

4. **Citation Verification**: every citation verified against Neo4j graph

### Unified LLM Gateway

**Design Decision**: Single LLM layer serves both Contract Review and Legal QA pipelines. Users interact naturally without switching modes — the system detects domain (QA vs Contract Review vs Mixed) and routes accordingly.

**Provider**: GPT 5.4 mini (configurable model + API key). Mock provider for development/testing.

**Conversation State**: System maintains conversation context to handle follow-up questions naturally:
```
User: "Review hợp đồng này"          → CONTRACT_REVIEW
User: "Tại sao điều khoản phạt sai?" → CONTRACT_QA (về kết quả review)
User: "Luật đó còn hiệu lực không?"  → QA (validity)
```

### Intent Analysis (T5.1) — Expanded Taxonomy

**Hierarchical Model**:

```
Level 1: Domain (System action)
├── QA                    → Hỏi về pháp luật
├── CONTRACT_REVIEW       → Review hợp đồng (có file đính kèm)
├── CONTRACT_QA           → Hỏi VỀ kết quả review hợp đồng
├── EXPLAIN               → Giải thích, làm rõ
└── CHITCHAT              → Không liên quan → fallback

Level 2: Intent (QA domain only)
├── LOOKUP                → Tra cứu văn bản/điều khoản
│   ├── granularity: "chapter" | "article" | "clause" | "point" | "document"
│   └── extracted: document_type, document_name, article_number, clause_number, point_label, so_ky_hieu
│
├── TOPIC                 → Hỏi về chủ đề
│   └── aspect: "regulations" | "procedures" | "penalties"
│
├── VALIDITY              → Hỏi hiệu lực
│   └── target: "document" | "article"
│
├── COMPARISON            → So sánh
│   ├── documents: [{document_type, document_name, year}, ...]
│   └── aspect: "content" | "validity" | "penalties"
│
├── CHECKLIST             → Hỏi danh sách yêu cầu
│   └── target: "contract_requirements" | "procedures"
│
├── NUMERIC               → Hỏi con số/giới hạn
│   └── metric: "penalty" | "threshold" | "deadline"
│
├── SCENARIO              → Hỏi tình huống cụ thể
│   └── context: {facts...}
│
└── SEARCH                → Tìm kiếm/tổng hợp
    └── scope: "documents" | "articles" | "topics"
```

**Multi-Intent Decomposition**: Complex queries are decomposed into sub-queries for parallel processing:
```
User: "Điều 17 Luật DN 2020 còn hiệu lực không, và khác gì Luật 2014?"
→ Sub-queries:
   1. LOOKUP(article=17, law="LT-068-2020") → direct_lookup
   2. VALIDITY(law="LT-068-2020") → validity_check
   3. COMPARISON(law1="LT-068-2020", law2="LT-059-2014") → comparison
```

**Confidence Handling**:
- confidence >= 0.7 → Proceed
- 0.4 <= confidence < 0.7 → Ask clarification
- confidence < 0.4 → Fallback to general QA or "Tôi chưa hiểu rõ"

**so_ky_hieu Resolution**: Resolved in T5.1 using lookup table from T0.1. T5.2 needs doc_id for direct lookup, so resolution cannot be delayed.

### Legal QA Pipeline

1. **Intent Analysis** (LLM): Classify domain + intent, decompose multi-intent queries into sub-queries, extract entities (document_type, article/clause/point numbers, so_ky_hieu, topic, time_reference)
2. **Retrieval**: article reference → direct graph lookup; topic query → vector search + graph traversal; comparison → parallel retrieval + diff
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
| LLM Provider | GPT 5.4 mini (configurable, with Mock for dev) | Unified for intent analysis, clause extraction, compliance, answer generation |
| Web Framework | Python (FastAPI) |
| Data Processing | Python (pandas, pyarrow) |
| Vector Search | Neo4j vector index |
| Contract Parsing | MinerU (Apache 2.0) + PII redaction layer |
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