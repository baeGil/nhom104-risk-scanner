## 1. Setup & Data Preparation

- [x] 1.1 Create `data/short_title_mapping.json` containing mappings for common laws (e.g., "Luật Đất đai", "Bộ luật Dân sự").
- [x] 1.2 Implement `preprocess_text` in `src/cross_reference/extractor.py` for whitespace normalization and semicolon-based fragmenting.

## 2. Extraction Implementation

- [x] 2.1 Implement `_extract_internal_refs` in `extractor.py` with support for alphanumeric article numbers (e.g., "48a").
- [x] 2.2 Implement `_extract_external_refs` in `extractor.py` with short-title lookup and serial number regex.
- [x] 2.3 Implement `_extract_modifications` in `extractor.py` to capture actions (sửa đổi, bổ sung, bãi bỏ) from text fragments.
- [x] 2.4 Implement `_extract_preamble_anchor` in `extractor.py` to identify the primary target document while avoiding historical metadata.

## 3. Writer & Validation

- [x] 3.1 Implement `CrossReferenceWriter` in `writer.py` using Cypher MERGE for article-level links.
- [x] 3.2 Implement `CrossReferenceValidator` in `validator.py` to report resolution rates and log unresolved references.
- [x] 3.3 Create a comprehensive test suite in `src/cross_reference/tests/` verifying all regex and logic edge cases.
