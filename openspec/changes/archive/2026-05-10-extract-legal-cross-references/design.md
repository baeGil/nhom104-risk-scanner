## Context

The current legal knowledge graph contains hierarchical document structures (Chương -> Điều -> Khoản -> Điểm) but lacks precise article-level relationships. While document-level metadata exists in `relationships.parquet`, it is often insufficient for determining exactly which provisions are being modified or referenced, and it lacks the granularity needed for Phase 3 (Effective Text Composition).

## Goals / Non-Goals

**Goals:**
- Extract precise `[:REFERENCES_INTERNAL]`, `[:REFERENCES_EXTERNAL]`, and `[:MODIFIES]` relationships from legal text.
- Resolve document references using both serial numbers (`so_ky_hieu`) and common short titles.
- Accurately determine the "Active" direction of modification (A modifies B) using preamble analysis.
- Handle multi-action modification clauses within a single sentence.

**Non-Goals:**
- Extraction of "Quyết định" (QĐ) references as per user preference.
- Resolution of implicit references (e.g., "theo quy định của pháp luật").
- Handling of pre-1999 law numbering formats that do not match standard patterns.

## Decisions

### 1. Semicolon-Based Pre-processing
**Decision**: Split article text by semicolons (`;`) before applying modification extraction regex.
**Rationale**: Many legal modification clauses list multiple actions in one sentence (e.g., "Sửa đổi khoản 1; bãi bỏ khoản 2"). Splitting them into fragments allows for simpler, more robust regex patterns compared to a single complex regex that tries to capture all permutations.

### 2. Preamble Anchor Strategy
**Decision**: Scan the document header (before Article 1) specifically for the primary target, stopping at the `"đã được"` keyword.
**Rationale**: The preamble defines the current document's identity. By isolating the primary target before the "history" section starts, we avoid creating redundant or incorrect historical relationships and ensure the `[:MODIFIES]` link points in the correct "Active" direction.

### 3. Static JSON Short-Title Mapping
**Decision**: Maintain a `short_title_mapping.json` file for common laws (e.g., "Luật Đất đai", "Bộ luật Dân sự").
**Rationale**: Using a static mapping is significantly faster and more accurate than fuzzy searching the entire 13k document database for every title mention. It provides a "quick win" for the most frequently referenced documents.

### 4. Alphanumeric Article Support
**Decision**: Update all article-level regex to use `\d+[a-zđ]?` instead of `\d+`.
**Rationale**: Vietnamese legal documents frequently insert new articles using suffixes like "48a", "48b". Standardizing on alphanumeric support ensures no provisions are missed.

## Risks / Trade-offs

- **[Risk] Regex Conflict** → [Mitigation] Use positive lookaheads for boundaries and prioritize more specific patterns (e.g., Point -> Clause -> Article) over generic ones.
- **[Risk] Missing Short Titles** → [Mitigation] Implement a fallback to fuzzy matching for `so_ky_hieu` and log all unresolved references to update the mapping table iteratively.
- **[Risk] Multiple Targets in one Fragment** → [Mitigation] The extractor will return a list of matches per fragment; the writer will iterate through them to create separate relationships.
