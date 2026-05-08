# Spec: Data Cleanup & Normalization

## Overview

Normalize, deduplicate, and enrich the raw dataset (metadata.parquet, content.parquet, relationships.parquet) to prepare clean, consistent input for the segmentation pipeline.

## Capabilities

### Normalize so_ky_hieu

Parse raw so_ky_hieu into structured components and generate a normalized form for cross-reference resolution.

- Parse 5 core document types: Luật, Bộ luật, Nghị định, Thông tư, Thông tư liên tịch
- Extract: type, number, year, session/issuer from raw so_ky_hieu
- Generate normalized form: `{TYPE_ABBREV}-{ZERO_PADDED_NUMBER}-{YEAR}[-{ISSUER}]`
- Standard abbreviations: Luật → LT, Bộ luật → BL, Nghị định → ND, Thông tư → TT, Thông tư liên tịch → TTLT
- Handle non-standard formats (old Sắc lệnh, early-format ND/TT without proper numbering)
- Handle "Không số" → skip normalization, flag for manual review
- Build lookup table mapping normalized so_ky_hieu → doc_id
- Resolution priority: exact match → fuzzy match (Levenshtein ≤ 2) → year + type + title substring → flag for manual
- Target: ≥95% resolution rate for standard formats, ≥80% for non-standard formats

### Deduplicate documents

Identify and merge documents with identical normalized so_ky_hieu + loai_van_ban + same year.

- 1,273 exact duplicates identified in current dataset
- Keep version with most content bytes; merge metadata preferring non-null fields
- Log all merge decisions with before/after record IDs
- Output: deduplicated metadata dataset

### Crawl missing content

Fill content gaps for 2,637 core documents missing from content.parquet.

- Search thuvienphapluat.vn using so_ky_hieu as search key
- Extract HTML content from document detail page
- Insert into content.parquet with matching doc_id
- Preserve all existing metadata fields unchanged
- Handle rate limiting and error cases (document not found, network error)
- Verify crawled content: must contain at least one Điều marker
- Target: ≥95% content coverage for effective core docs

### Clean HTML

Standardize HTML content for consistent parsing.

- Strip wrapper `<table class="detailcontent">` and `<tr>/<td>` structural tags
- Remove `<font>` tags (keep content, drop inline formatting)
- Remove empty `<p>` tags (containing only whitespace or `&nbsp;`)
- Remove `<dir>` tags
- Normalize `<p>` spacing
- Preserve `<b>`, `<strong>` markers (essential for hierarchy detection)
- Preserve `<i>`, `<em>` markers (legal definitions, case references)
- Preserve `<table>` content within articles (tables of fees, schedules)
- Store both raw_html (original) and clean_html (processed) columns
- Verify: clean_html must retain all text content from raw_html