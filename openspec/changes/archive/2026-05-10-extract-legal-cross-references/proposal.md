## Why

Existing metadata in `relationships.parquet` provides only document-level links and is often inconsistent in direction (mixing "modifies" and "is modified by"). For Phase 3 (Effective Text Composition), we need precise, article-level relationships ("Khoản 1 Điều 5 Luật A sửa đổi Điều 10 Luật B") extracted directly from the legal text to ensure the "legal truth" is preserved.

## What Changes

- **Short-Title Resolution**: Implementation of a mapping table to resolve references using common titles (e.g., "Luật Đất đai") instead of full serial numbers.
- **Article-Level Extraction**: Robust regex-based extraction of internal (same document) and external (other documents) references at the Article/Clause/Point level.
- **Modification Logic**: Specialized extraction of amendment actions (sửa đổi, bổ sung, thay thế, bãi bỏ) with support for multi-action sentence splitting.
- **Preamble Anchor**: Extraction of the primary target document from the preamble (before the "đã được" history section) to establish the authoritative document-level relationship direction.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `cross-reference-extraction`: Adding short-title mapping, preamble anchoring, multi-action splitting, and alphanumeric article number support (e.g., "48a").

## Impact

- `src/cross_reference/`: Implementation of `extractor.py`, `models.py`, `writer.py`, and `validator.py`.
- `Neo4j`: Creation of `[:REFERENCES_INTERNAL]`, `[:REFERENCES_EXTERNAL]`, and `[:MODIFIES]` relationships.
- `Phase 3`: This change is a prerequisite for any automated legal text merging or "Văn bản hợp nhất" logic.
