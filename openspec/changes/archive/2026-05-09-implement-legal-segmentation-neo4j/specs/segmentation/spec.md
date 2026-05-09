## MODIFIED Requirements

### Requirement: Ingest into Neo4j
Batch import parsed segments into Neo4j graph database.

- Create database schema: node labels, relationship types, property types
- Create uniqueness constraints on Document.id, Article.uid, Clause.uid, Point.uid
- Create indexes: Document.so_ky_hieu, Document.loai_van_ban, Document.tinh_trang_hieu_luc, Article.uid, Article.is_current
- Create fulltext indexes: Document (title, so_ky_hieu), Article (title, clean_text)
- **MODIFIED**: Create vector index: Article.embedding (1024 dims, cosine similarity)
- Use MERGE operations for idempotency (not CREATE)
- Batch size: 5,000 nodes per transaction
- Ingest order: Document → Chapter → Article → Clause → Point
- Create HAS_CHAPTER, HAS_ARTICLE, HAS_CLAUSE, HAS_POINT relationships with order property
- Target: ~900K segment nodes

#### Scenario: Ingest with 1024-dim vector index
- **WHEN** Neo4j schema is initialized
- **THEN** Article.embedding vector index MUST be configured with 1024 dimensions.

### Requirement: Generate Article embeddings
Embed Article.clean_text using mainguyen9/vietlegal-harrier-0.6b (or upgraded model).

- Load model locally (self-hosted, no API cost)
- Batch process: embed all Article nodes' clean_text
- **MODIFIED**: Store in Article.embedding property (1024-dimensional float array)
- Batch size: 512 articles per embedding batch
- **MODIFIED**: Verify: embedding dimension must be 1024 for all articles
- Create Neo4j vector index for similarity search

#### Scenario: Verify 1024-dim embeddings
- **WHEN** Embedding generation is complete
- **THEN** Each Article node MUST contain an embedding vector of exactly 1024 elements.

### Requirement: Parse legal document hierarchy
Implement a state machine that processes cleaned HTML top-to-bottom, detecting Vietnamese legal document structural elements.

- Detect Chương (Chapter): `/^Chương\s+[IVXL]+\s*\.?\s/i`
- Detect Điều (Article): `/^[Đđ][ií]ều\s+\d+[\.:\s]/`
- Detect Khoản (Clause): `/^\d+\.\s/` (contextual — only valid after a Điều)
- Detect Điểm (Point): `/^[a-z]\)\s/` and `/^[ivx]+\)\s/` (after Khoản)
- **MODIFIED**: Detect Mục (Section): `/^Mục\s+\d+\.?\s/i`. Sections SHALL be treated as metadata (stored in `section` property of following Articles) rather than separate nodes.
- State machine tracks current Chapter → Article → Clause → Point context
- Điều resets Khoản counter; Khoản resets Điểm counter
- **ADDED**: Encountering a higher-level element (Phần, Chương) SHALL reset the current Section (Mục) context.
- Skip "Căn cứ..." preamble sections (not hierarchical elements)
- Table content attached to parent clause/article
- Handle documents without chapters (many ND/TT have flat Điều structure)
- Handle documents with both `<b>Điều` and `<strong>Điều` formatting
- Output: segments list with (doc_id, hierarchy_type, index, path, text_content, clean_text, parent_uid, section)

#### Scenario: Section metadata inheritance
- **WHEN** Parser detects "Mục 1" followed by "Điều 5"
- **THEN** The Article node for Điều 5 MUST have a `section` property with value "Mục 1".

#### Scenario: Section context reset
- **WHEN** Parser is in "Mục 2" of "Chương I" and detects "Chương II"
- **THEN** The next Article detected SHALL NOT have "Mục 2" in its `section` property.
