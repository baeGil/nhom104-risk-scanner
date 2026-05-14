## MODIFIED Requirements

### Extract external references
The system SHALL detect references from one document's provisions to provisions in other documents.

- **Pre-normalization**: Strip whitespace around delimiters (e.g., `46 / 2014` -> `46/2014`) before matching.
- **Short Title Support**: Resolve references using common titles (e.g., "Luật Đất đai") via a dedicated mapping table to `so_ky_hieu`.
- Regex patterns for cross-document references:
  - `"căn cứ Luật {keyword} số {N}/{Y}/QH{session}"` → Luật lookup
  - `"theo Nghị định {N}/{Y}/NĐ-CP"` → Nghị định lookup
  - `"theo Thông tư số {N}/{Y}/TT-{agency}"` → Thông tư lookup
  - `"theo Bộ luật {keyword} số {N}/{Y}/QH{session}"` → Bộ luật lookup
  - `"theo Thông tư liên tịch số {N}/{Y}/TTLT-{agency}"` → TTLT lookup
- Resolve to Document nodes via so_ky_hieu lookup table.
- When reference includes specific Điều/Khoản/Điểm: resolve to Article/Clause/Point within target document.
- **Stubbing Support**: Nếu văn bản đích hoặc Điều/Khoản/Điểm đích không tồn tại trong Database, hệ thống SHALL tạo node Stub (với thuộc tính `is_stub: true`) thay vì bỏ qua.
- Fuzzy match fallback for ~25-30% non-standard formats:
  - Levenshtein distance ≤ 2 on so_ky_hieu
  - Year + loai_van_ban + title substring containment
- Create [:REFERENCES_EXTERNAL] relationships with context and target_so_ky_hieu.
- Target: ≥95% resolution rate for standard formats, ≥80% for non-standard.

#### Scenario: Resolve external reference with stubbing
- **WHEN** một dẫn chiếu ngoại được tìm thấy nhưng văn bản đích không tồn tại trong Neo4j
- **THEN** hệ thống SHALL tạo một node `Document` stub và thực hiện kết nối quan hệ bình thường.

### Extract modification references
The system SHALL parse "sửa đổi/bổ sung" documents to create article-level modification links.

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
- Resolve target_document to Neo4j Document node via so_ky_hieu lookup.
- Resolve target_article to Article node within target document.
- **Stubbing Support**: Nếu văn bản đích hoặc Điều đích không tồn tại, hệ thống SHALL tạo node Stub (Document/Article) để duy trì quan hệ sửa đổi.
- Create [:MODIFIES] relationships with full metadata (action, target_clause, target_point, context)
- Validate: source Article must exist, target Document must exist (or be created as stub), target Article should exist (or be created as stub).
- Target: 5,000-8,000 article-level modification links.

#### Scenario: Handle modification of missing article
- **WHEN** văn bản đang sửa đổi một Điều không tồn tại trong database
- **THEN** hệ thống SHALL tạo một node `Article` stub thuộc về văn bản đích đó và nối quan hệ `[:MODIFIES]`.
