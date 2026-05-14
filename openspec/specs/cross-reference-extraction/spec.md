# Spec: Cross-Reference Extraction

## Overview

Extract article-level cross-references (internal, external, and modification references) from parsed segment text and create relationships in Neo4j.

## Capabilities

### Extract internal references

Detect references from one Điều/Khoản/Điểm to another within the same document.

- Regex patterns for same-document references:
  - `"theo quy định tại Điều {N}"` → Article N
  - `"tại khoản {K} Điều {N}"` → Article N, Clause K
  - `"tại điểm {L} khoản {K} Điều {N}"` → Article N, Clause K, Point L
  - `"như quy định tại Điều {N} và Điều {M}"` → two internal references
  - `"theo khoản {K} và khoản {K2} Điều {N}"` → two clause references
  - `"tại các Điều {N}, {M}, {P}"` → multiple article references
- Handle Vietnamese number words: "một" → 1, "hai" → 2 (rare in legal text but possible)
- Resolve to Article/Clause/Point nodes within the same Document
- Create [:REFERENCES_INTERNAL] relationships with context text (original phrase where reference was found)
- Target: ~100K internal reference relationships across all documents

### Extract external references

Detect references from one document's provisions to provisions in other documents.

- **Pre-normalization**: Strip whitespace around delimiters (e.g., `46 / 2014` -> `46/2014`) before matching.
- **Short Title Support**: Resolve references using common titles (e.g., "Luật Đất đai") via a dedicated mapping table to `so_ky_hieu`.
- Regex patterns for cross-document references:
  - `"căn cứ Luật {keyword} số {N}/{Y}/QH{session}"` → Luật lookup
  - `"theo Nghị định {N}/{Y}/NĐ-CP"` → Nghị định lookup
  - `"theo Thông tư số {N}/{Y}/TT-{agency}"` → Thông tư lookup
  - `"theo Bộ luật {keyword} số {N}/{Y}/QH{session}"` → Bộ luật lookup
  - `"theo Thông tư liên tịch số {N}/{Y}/TTLT-{agency}"` → TTLT lookup
- Resolve to Document nodes via so_ky_hieu lookup table
- When reference includes specific Điều/Khoản/Điểm: resolve to Article/Clause/Point within target document
- **Stubbing Support**: Nếu văn bản đích hoặc Điều/Khoản/Điểm đích không tồn tại trong Database, hệ thống SHALL tạo node Stub (với thuộc tính `is_stub: true`) thay vì bỏ qua.
- Fuzzy match fallback for ~25-30% non-standard formats:
  - Levenshtein distance ≤ 2 on so_ky_hieu
  - Year + loai_van_ban + title substring containment
- Create [:REFERENCES_EXTERNAL] relationships with context and target_so_ky_hieu
- Unresolved references logged for manual review
- Target: ≥95% resolution rate for standard formats, ≥80% for non-standard

### Extract modification references

Parse "sửa đổi/bổ sung" documents to create article-level modification links.

- **Multi-action Split**: Pre-process text by splitting sentences on semicolons (`;`) to handle multiple actions (e.g., "Sửa đổi khoản 1; bãi bỏ khoản 2").
- Only process documents identified in relationship data as "Văn bản sửa đổi" or "Văn bản bổ sung"
- For each Điều of the modifying document, parse its text to extract:
  - Action: "sửa đổi" | "bổ sung" | "thay thế" | "bãi bỏ" | "hết hiệu lực một phần"
  - Target document: so_ky_hieu reference in text (including short titles) → resolve to doc_id
  - Target article: Điều number extracted from text
  - Target clause: Khoản number (nullable)
  - Target point: Điểm letter (nullable)
  - Source text: original phrase where modification was found
- Common patterns:
  - `"Sửa đổi khoản {K} Điều {Z} {Loại_văn_ban} số {so_ky_hieu}"`
  - `"Bổ sung điểm {L} khoản {K} Điều {Z} như sau: ..."`
  - `"Thay thế cụm từ '...' tại Điều {Z} khoản {K} bằng '...'"`
  - `"Bãi bỏ khoản {K} Điều {Z}"`
  - `"Sửa đổi, bổ sung một số khoản của Điều {Z} ..."`
- Resolve target_document to Neo4j Document node via so_ky_hieu lookup
- Resolve target_article to Article node within target document
- **Stubbing Support**: Nếu văn bản đích hoặc Điều đích không tồn tại, hệ thống SHALL tạo node Stub (Document/Article) để duy trì quan hệ sửa đổi.
- Create [:MODIFIES] relationships with full metadata (action, target_clause, target_point, context)
- Validate: source Article must exist, target Document must exist, target Article should exist
- Log unresolved modifications (target_doc or target_article not found)
- Target: 5,000-8,000 article-level modification links

### Extract primary target from preamble

For amending documents, extract the primary target document mentioned in the preamble to establish a high-confidence document-level MODIFIES relationship.

- **Scope**: Only scan the text from the beginning of the document up to the first occurrence of `"đã được"` or the first Article.
- **Regex Pattern**: `sửa đổi,\s+bổ sung\s+một số điều của\s+([^,;]+?)\s+số\s+(\d+/\d+/[A-ZĐ-]+)`
- **Logic**:
  - Identify the primary document being amended.
  - Resolve to `doc_id` via `so_ky_hieu` lookup.
  - Create a document-level `[:MODIFIES]` relationship in Neo4j.
- **Purpose**: This acts as the "anchor" for all article-level modifications found in the body, ensuring the correct direction of the relationship (Current Doc -> Modifies -> Target Doc).

### Validate cross-references

Verify that all extracted relationships point to valid nodes in Neo4j.

- Check all [:REFERENCES_EXTERNAL] targets resolve to existing Document nodes
- Check all [:MODIFIES] targets resolve to existing Article nodes
- Check internal references resolve within same Document
- Compute resolution rate metrics:
  - Standard format resolution rate
  - Non-standard format resolution rate
  - Overall resolution rate
- Generate validation report with:
  - Total references extracted by type
  - Resolution rate by type
  - List of unresolved references (for manual review)
  - Distribution of confidence scores for fuzzy matches
- Target: ≥95% overall resolution rate, ≥95% for standard formats, ≥80% for non-standard