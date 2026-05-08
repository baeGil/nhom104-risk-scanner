# Spec: Segmentation

## Overview

Parse legal document HTML content into a hierarchical structure of segments (Chương → Điều → Khoản → Điểm) and ingest into Neo4j with embeddings.

## Capabilities

### Parse legal document hierarchy

Implement a state machine that processes cleaned HTML top-to-bottom, detecting Vietnamese legal document structural elements.

- Detect Chương (Chapter): `/^Chương\s+[IVXL]+\s*\.?\s/i`
- Detect Điều (Article): `/^[Đđ][ií]ều\s+\d+[\.:\s]/`
- Detect Khoản (Clause): `/^\d+\.\s/` (contextual — only valid after a Điều)
- Detect Điểm (Point): `/^[a-z]\)\s/` and `/^[ivx]+\)\s/` (after Khoản)
- Detect Mục (Section): `/^Mục\s+\d+\.?\s/i`
- State machine tracks current Chapter → Article → Clause → Point context
- Điều resets Khoản counter; Khoản resets Điểm counter
- Skip "Căn cứ..." preamble sections (not hierarchical elements)
- Table content attached to parent clause/article
- Handle documents without chapters (many ND/TT have flat Điều structure)
- Handle documents with both `<b>Điều` and `<strong>Điều` formatting
- Output: segments list with (doc_id, hierarchy_type, index, path, text_content, clean_text, parent_uid)

### Compute confidence score

Each parsed document receives a confidence score reflecting parse quality.

- High (≥0.9): ≥80% of expected Điều detected based on document metadata cross-references, clear formatting, no structural anomalies
- Medium (0.6-0.9): some misalignment between detected and expected structure, requires review
- Low (<0.6): poor structure, significant parsing errors, flag for LLM fallback (future phase)
- Confidence factors: ratio of detected Điều to expected (based on cross-references), formatting consistency, presence of `<b>`/`<strong>` markers for headings, completeness of hierarchy
- Generate per-document confidence report with specific failure indicators
- Target: ≥80% of effective core docs parsed with High confidence, ≤5% Low confidence

### Parse all effective core documents

Run parser on cleaned HTML content for all 12,921 effective core documents (Luật, ND, TT, TTLT).

- Process documents in order of importance: Luật → ND → TT → TTLT
- Generate segments for each document with proper hierarchy
- Track: total documents parsed, confidence distribution, failure count
- Log all Low-confidence documents for review
- Output: complete segments dataset ready for Neo4j ingestion

### Ingest into Neo4j

Batch import parsed segments into Neo4j graph database.

- Create database schema: node labels, relationship types, property types
- Create uniqueness constraints on Document.id, Article.uid, Clause.uid, Point.uid
- Create indexes: Document.so_ky_hieu, Document.loai_van_ban, Document.tinh_trang_hieu_luc, Article.uid, Article.is_current
- Create fulltext indexes: Document (title, so_ky_hieu), Article (title, clean_text)
- Create vector index: Article.embedding (768 dims, cosine similarity)
- Use MERGE operations for idempotency (not CREATE)
- Batch size: 5,000 nodes per transaction
- Ingest order: Document → Chapter → Article → Clause → Point
- Create HAS_CHAPTER, HAS_ARTICLE, HAS_CLAUSE, HAS_POINT relationships with order property
- Target: ~900K segment nodes

### Generate Article embeddings

Embed Article.clean_text using mainguyen9/vietlegal-harrier-0.6b.

- Load model locally (self-hosted, no API cost)
- Batch process: embed all Article nodes' clean_text
- Store in Article.embedding property (768-dimensional float array)
- Batch size: 512 articles per embedding batch
- Verify: embedding dimension must be 768 for all articles
- Create Neo4j vector index for similarity search

### Ingest document-level relationships

Migrate 659K relationships from relationships.parquet into Neo4j.

- Map relationship types from Vietnamese to Neo4j relationship types:
  - "Văn bản căn cứ" → CITES
  - "Văn bản dẫn chiếu" → REFERRED_BY
  - "Văn bản HD, QĐ chi tiết" → DETAILS
  - "Văn bản được HD, QĐ chi tiết" → DETAILED_BY
  - "Văn bản hết hiệu lực" → SUPERSEDED_BY
  - "Văn bản quy định hết hiệu lực" → SUPERSEDES
  - "Văn bản bị hết hiệu lực 1 phần" → PARTIALLY_SUPERSEDED_BY
  - "Văn bản quy định hết hiệu lực 1 phần" → PARTIALLY_SUPERSEDES
  - "Văn bản sửa đổi" → AMENDS
  - "Văn bản được sửa đổi" → AMENDED_BY
  - "Văn bản bổ sung" → SUPPLEMENTS
  - "Văn bản được bổ sung" → SUPPLEMENTED_BY
  - "Văn bản liên quan khác" → RELATED
  - "Văn bản đình chỉ" / "Văn bản bị đình chỉ" → SUSPENDED_BY / SUSPENDS
  - "Văn bản đình chỉ 1 phần" / "Văn bản bị đình chỉ 1 phần" → PARTIALLY_SUSPENDED_BY / PARTIALLY_SUSPENDS
- Create both forward and reverse relationships
- Validate: both doc_id and other_doc_id must exist as Document nodes
- Log any orphan relationships (doc_id not found in Document nodes)