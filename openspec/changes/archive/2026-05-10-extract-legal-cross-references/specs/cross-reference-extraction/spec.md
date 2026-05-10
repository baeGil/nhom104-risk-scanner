## MODIFIED Requirements

### Extract external references
The system SHALL detect references from one document's provisions to provisions in other documents.
- **Pre-normalization**: Strip whitespace around delimiters (e.g., `46 / 2014` -> `46/2014`) before matching.
- **Short Title Support**: Resolve references using common titles (e.g., "Luật Đất đai") via a dedicated mapping table to `so_ky_hieu`.
- **Fuzzy match fallback**: Levenshtein distance ≤ 2 on so_ky_hieu or Year + loai_van_ban + title substring containment.
- **Output**: Create `[:REFERENCES_EXTERNAL]` relationships with context and target_so_ky_hieu.

#### Scenario: Resolve via short title
- **WHEN** text contains "theo quy định tại Luật Đất đai"
- **THEN** system resolves "Luật Đất đai" to `31/2024/QH15` using mapping table and creates relationship.

#### Scenario: Pre-normalization of serial number
- **WHEN** text contains "Nghị định số 46 / 2014 / NĐ-CP"
- **THEN** system normalizes to "46/2014/NĐ-CP" and resolves to correct Document node.

### Extract modification references
The system SHALL parse "sửa đổi/bổ sung" documents to create article-level modification links.
- **Multi-action Split**: Pre-process text by splitting sentences on semicolons (`;`) to handle multiple actions.
- **Action extraction**: Support "sửa đổi", "bổ sung", "thay thế", "bãi bỏ", "hết hiệu lực một phần".
- **Alphanumeric articles**: Support article numbers like "48a", "48b".
- **Output**: Create `[:MODIFIES]` relationships with action, target_clause, target_point, and context.

#### Scenario: Handle multi-action sentence
- **WHEN** text is "Sửa đổi khoản 1; bãi bỏ khoản 2 Điều 5"
- **THEN** system splits into two fragments and creates two separate MODIFIES relationships.

#### Scenario: Capture alphanumeric article
- **WHEN** text is "Sửa đổi Điều 48a của Luật X"
- **THEN** system captures "48a" as the target article index.

## ADDED Requirements

### Extract primary target from preamble
For amending documents, the system SHALL extract the primary target document mentioned in the preamble to establish a high-confidence document-level MODIFIES relationship.
- **Scope**: Only scan the text from the beginning of the document up to the first occurrence of `"đã được"` or the first Article.
- **Regex Pattern**: `sửa đổi,\s+bổ sung\s+một số điều của\s+([^,;]+?)\s+số\s+(\d+/\d+/[A-ZĐ-]+)`
- **Logic**: Resolve to `doc_id` and create a document-level `[:MODIFIES]` relationship.

#### Scenario: Extract anchor from complex preamble
- **WHEN** preamble contains "Luật sửa đổi, bổ sung... của Luật X số 15/2012/QH13 đã được sửa đổi..."
- **THEN** system stops before "đã được" and extracts "Luật X" with serial "15/2012/QH13" as the primary target.
