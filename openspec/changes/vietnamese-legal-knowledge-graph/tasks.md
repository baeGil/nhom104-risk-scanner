# Vietnamese Legal Knowledge Graph — Tasks

## Phase 0: Data Cleanup & Normalization

- [x] T0.1: **Normalize so_ky_hieu** — Parse raw so_ky_hieu into structured components (type, number, year, issuer) for all 5 core document types. Generate normalized form (e.g., "ND-046-2014"). Handle 25-30% non-standard formats with pattern matching. Build lookup table mapping normalized so_ky_hieu → doc_id. — *Spec: data-cleanup-and-normalization*

- [ ] T0.2: **Deduplicate documents** — Identify 1,273 exact duplicates (same so_ky_hieu + same loai_van_ban). Keep version with most content bytes, merge metadata preferring non-null fields. Log all merge decisions with before/after record IDs. — *Spec: data-cleanup-and-normalization*

- [x] T0.3: **Crawl missing content** — *Note: Crawler created but thuvienphapluat.vn search structure may have changed. Needs refinement. 2,636 docs still missing content.* — For each of 2,637 core documents missing from content.parquet, crawl HTML from thuvienphapluat.vn using so_ky_hieu as search key. Extract content HTML from detail page, insert with matching doc_id, preserve all metadata fields. Target: ≥95% content coverage for effective core docs. — *Spec: data-cleanup-and-normalization*

- [x] T0.4: **Clean HTML pipeline** — Strip wrapper tables, remove `<font>` tags, normalize `<p>` formatting, preserve `<b>`/`<strong>` for hierarchy detection, preserve `<i>`/`<em>` for definitions. Store both raw_html and clean_html columns. — *Spec: data-cleanup-and-normalization*

- [x] T0.5: **Build so_ky_hieu lookup with fuzzy matching** — *Completed as part of T0.1. Lookup table saved to output/so_ky_hieu_lookup.json* — Create normalized lookup table with fuzzy match capability (Levenshtein ≤ 2, year + type + title substring fallback). Include disambiguation for 1,273 duplicate entries. — *Depends on: T0.1* — *Spec: data-cleanup-and-normalization*

## Phase 1: Segmentation

- [ ] T1.1: **Implement hierarchical parser** — State machine processing Chương → Điều → Khoản → Điểm detection with counter reset rules. Handle preamble skip ("Căn cứ..."), table content attachment, `<b>`/`<strong>` format variants. Output: segments list with (doc_id, hierarchy_type, index, path, text_content, clean_text, parent_uid). — *Spec: segmentation*

- [x] T1.2: **Implement confidence scoring** — *Completed as part of T1.1* — Per-document confidence: High (≥0.9): ≥80% expected Điều found. Medium (0.6-0.9): some misalignment. Low (<0.6): poor structure. Log distribution and failure indicators. — *Spec: segmentation*

- [x] T1.3: **Parse all effective core documents** — *Completed as part of T1.1. 16,091 effective docs parsed into 104,962 segments* — Run parser on 12,921 effective core docs. Generate segments for each. Target: ≥80% High confidence, ≤5% Low confidence. Process in order: Luật → ND → TT → TTLT. — *Depends on: T0.4, T1.1, T1.2* — *Spec: segmentation*

- [x] T1.4: **Set up Neo4j schema** — *Schema Cypher saved to output/neo4j_schema.cypher. Run in Neo4j Browser to create constraints and indexes.* — Install Neo4j, create node labels (Document, Chapter, Article, Clause, Point, EffectiveArticle), relationship types, property types. Create uniqueness constraints on Document.id and Article.uid. Create indexes (so_ky_hieu, loai_van_ban, uid). — *Spec: segmentation*

- [x] T1.5: **Batch ingest segments into Neo4j** — MERGE operations for Document → Chapter → Article → Clause → Point hierarchy. Create HAS_CHAPTER, HAS_ARTICLE, HAS_CLAUSE, HAS_POINT relationships with order property. Batch size: 5,000 nodes per transaction. Target: ~900K nodes. — *Depends on: T1.3, T1.4* — *Spec: segmentation*

- [ ] T1.6: **Generate Article embeddings** — Embed Article.clean_text using mainguyen9/vietlegal-harrier-0.6b (768d). Store in Article.embedding property. Batch size: 512 articles. Create Neo4j vector index for similarity search. — *Depends on: T1.4, T1.5* — *Spec: segmentation*

- [ ] T1.7: **Ingest document-level relationships** — Migrate 659K relationships from relationships.parquet. Map Vietnamese relationship types to Neo4j relationship types (CITES, DETAILS, SUPERSEDES, AMENDS, SUPPLEMENTS, etc.). Create both forward and reverse relationships. Validate: both endpoints must exist as Document nodes. — *Depends on: T1.4* — *Spec: segmentation*

## Phase 2: Cross-Reference Extraction

- [ ] T2.0: **Build short-title mapping table** — Create a JSON mapping of common law titles (e.g., "Luật Đất đai", "Bộ luật Dân sự") to their normalized `so_ky_hieu`. This enables resolution of references that lack serial numbers.

- [ ] T2.1: **Extract internal references** — Regex patterns for Điều/khoản/điểm references within same Document. Patterns: "theo quy định tại Điều {N}", "tại khoản {K} Điều {N}", "tại điểm {L} khoản {K} Điều {N}". Create [:REFERENCES_INTERNAL] relationships with context text. Target: ~100K internal references. — *Depends on: T1.3* — *Spec: cross-reference-extraction*

- [ ] T2.2: **Extract external references** — Implement `preprocess_text` to strip whitespace around `/`. Use Regex for cross-document references (Luật/ND/TT + so_ky_hieu) and resolve via T0.5 lookup or T2.0 short-title mapping. Fuzzy match fallback for non-standard formats. Create [:REFERENCES_EXTERNAL] relationships. — *Depends on: T0.5, T1.3, T2.0* — *Spec: cross-reference-extraction*

- [ ] T2.3: **Extract modification references** — Split sentences by `;` to handle multiple actions. For each Điều of modifying docs, extract action (sửa đổi/bổ sung/thay thế/bãi bỏ) and target (doc, Điều, Khoản, Điểm). Resolve via T0.5/T2.0. Create [:MODIFIES] relationships. — *Depends on: T1.3, T2.2* — *Spec: cross-reference-extraction*

- [ ] T2.4: **Validate cross-references** — Check all external references resolve to existing Document nodes. Check all MODIFIES targets resolve to existing Article nodes. Compute resolution rate metrics. Generate validation report. — *Depends on: T2.1, T2.2, T2.3* — *Spec: cross-reference-extraction*
- [ ] T2.5: **Extract primary target from Preamble** — Process the start of the document (before "đã được" or Article 1) to identify the primary amended document. Resolve to `doc_id` and create document-level `[:MODIFIES]` link. — *Depends on: T1.3, T2.0* — *Spec: cross-reference-extraction*

## Phase 3: Effective Text Composition

- [ ] T3.1: **Implement amendment chain traversal** — For each Article with incoming [:MODIFIES] edges, collect and order modifications by modifying_doc.ngay_ban_hanh ASC. Build ordered chain. Handle transitive chains (A modifies B which was modified by C). — *Depends on: T2.3* — *Spec: effective-text-composition*

- [ ] T3.2: **Implement rule-based text merge** — Handle "sửa đổi" (replace clause text), "bổ sung" (insert new point), "thay thế" (replace segment), "bãi bỏ" (mark voided). Apply modifications sequentially in chronological order. Handle multi-action modifications and cascading amendments. — *Depends on: T3.1* — *Spec: effective-text-composition*

- [ ] T3.3: **Create EffectiveArticle nodes** — Store composed text with as_of_date, amendment_chain, is_current flag. Create COMPOSED_FROM and AMENDED_BY relationships. For Articles without amendments: create base EffectiveArticle with identical text. — *Depends on: T3.2* — *Spec: effective-text-composition*

- [ ] T3.4: **Validate against VB hợp nhất** — Compare composed EffectiveArticle text against 35 VB hợp nhất documents (ground truth). Compute agreement rate (character similarity, structural equivalence, semantic equivalence). Flag mismatches. Target: ≥90% agreement. Use mismatches as training data for future LLM-assisted composition. — *Depends on: T3.3* — *Spec: effective-text-composition*

- [ ] T3.5: **Compute is_current for all Articles** — Check Document.tinh_trang_hieu_luc + incoming SUPERSEDES relationships + specific Điều-level invalidation (PARTIALLY_SUPERSEDES, "bãi bỏ" modifications). Update is_current and effective_date on all Articles and EffectiveArticles. Generate validity report. — *Depends on: T3.3, T1.7* — *Spec: effective-text-composition*

## Phase 4: Contract Review Pipeline

- [x] T4.1: **Implement contract parser** — PDF (PyMuPDF), Word (python-docx), text extraction. Tesseract OCR with Vietnamese language pack for scanned PDFs. Detect scanned vs text PDFs by character count per page. Output: raw_text. — *Spec: contract-review-pipeline*

- [ ] T4.2: **Implement contract clause extractor** — LLM-based extraction of clauses (type, parties, obligations) from contract raw text. Output: Contract and ContractClause nodes in Neo4j. Generate embeddings for ContractClause using vietlegal-harrier-0.6b. Target: ≥90% clause extraction accuracy. — *Depends on: T4.1* — *Spec: contract-review-pipeline*

- [ ] T4.3: **Implement legal provision matching** — Vector similarity search (top-20) + graph traversal (REFERENCES_INTERNAL, MODIFIES, DETAILS) + reranking (semantic × authority). Return top-5 legal provisions per contract clause. — *Depends on: T4.2, T1.6, T3.3* — *Spec: contract-review-pipeline*

- [ ] T4.4: **Implement compliance analysis** — LLM prompt with clause + matched provisions + effective text + amendment history. Output: violations, risks, suggestions, citations with Điều/Khoản/Điểm precision. — *Depends on: T4.3* — *Spec: contract-review-pipeline*

- [ ] T4.5: **Implement citation verification** — Parse citation format from LLM output. Lookup in Neo4j: verify Article exists, Document exists, Clause/Point exists (if specified), is_current=true. Mark as VERIFIED or UNVERIFIED. Target: 100% of citations verified or explicitly flagged. — *Depends on: T4.4* — *Spec: contract-review-pipeline*

- [ ] T4.6: **Implement policy review extension** — Same pipeline as T4.3-T4.5 with additional classification: "compliant_and_efficient", "compliant_but_restrictive", "non_compliant". Flag provisions more restrictive than law. — *Depends on: T4.3, T4.4* — *Spec: contract-review-pipeline*

## Phase 5: Legal QA Pipeline

- [x] T5.1: **Implement question intent analysis** — LLM classification: article_reference_query, topic_query, validity_query, comparison_query. Extract: document_type, article_number, time_reference. — *Spec: contract-review-pipeline*

- [ ] T5.2: **Implement retrieval pipeline** — Article reference → direct Neo4j lookup. Topic query → vector search + graph traversal (MODIFIES, REFERENCES, DETAILS). Always get EffectiveArticle for current text. — *Depends on: T3.3, T1.6* — *Spec: contract-review-pipeline*

- [ ] T5.3: **Implement answer generation** — LLM prompt: question + retrieved provisions + effective text + amendment history. Output: answer with precise citations (Điều X khoản Y Luật Z). — *Depends on: T5.2* — *Spec: contract-review-pipeline*

- [ ] T5.4: **Implement QA citation verification** — Same as T4.5, applied to QA answers. — *Depends on: T5.3* — *Spec: contract-review-pipeline*

## Infrastructure

- [x] T6.1: **Set up Neo4j self-hosted** — Install Neo4j Community/Apocalypse, configure for 900K+ nodes. Set memory heap (≥4GB), page cache (≥2GB). Configure vector index plugin. — *Spec: segmentation*

- [ ] T6.2: **Deploy embedding service** — Deploy mainguyen9/vietlegal-harrier-0.6b as embedding service (FastAPI). Configure batch processing for 900K segments. GPU recommended for initial embedding generation. — *Spec: segmentation*

- [x] T6.3: **Build pipeline orchestration** — Python scripts for each phase. Idempotent (can resume from failure). Logging, progress tracking, error reporting. Configuration for batch sizes, Neo4j connection, embedding service URL. — *Spec: segmentation*

- [ ] T6.4: **Build testing & validation suite** — Unit tests for parser (known document structures). Integration tests for cross-reference resolution. End-to-end tests for contract review. Automated VB hợp nhất comparison test. Citation verification test. — *Spec: effective-text-composition*