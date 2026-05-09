## Context

T4.1 (Contract Parser) is the first task in the Contract Review Pipeline (Phase 4). The original spec called for PyMuPDF + python-docx + Tesseract OCR. After exploration, we decided to use MinerU (Apache 2.0) for better Vietnamese support, unified multi-format handling, and structured Markdown output.

The parser output feeds T4.2 (Clause Extraction), which uses LLM to extract clauses. Structured Markdown from MinerU makes clause boundary detection easier than raw text.

PII detection is needed because contracts contain sensitive personal/business data (CCCD, phone, email, bank accounts) that should be redacted before LLM processing.

## Goals / Non-Goals

**Goals:**
- Parse PDF, DOCX, TXT contracts to structured Markdown
- Auto-detect and handle scanned PDFs via MinerU's built-in OCR
- Detect and redact Vietnamese PII (CCCD, phone, email, MST, address, bank account)
- Output both raw and redacted text with reversible PII mapping
- Provide clean interface for downstream T4.2 (clause extraction)

**Non-Goals:**
- Clause extraction (T4.2) — parser only extracts text, not clauses
- LLM integration — no LLM calls in T4.1
- Web UI — CLI/library only
- Real-time processing — batch/single-file processing

## Decisions

### 1. MinerU over PyMuPDF + Tesseract

**Decision**: Use `mineru` package (Apache 2.0) as the primary document parser.

**Rationale**:
- Single library vs. 3+ libraries (PyMuPDF, python-docx, Tesseract)
- Built-in Vietnamese OCR (109 languages)
- Auto header/footer removal
- Structured Markdown output (benefits T4.2)
- Active development (62k+ stars)

**Alternatives considered**:
- Mely-PDF-Miner (Vietnamese fork): AGPL-3.0 license, low activity (4 stars, last update Nov 2024)
- PyMuPDF + Tesseract: More control but complex setup, Vietnamese OCR requires manual config

### 2. PII Detection via Regex Patterns

**Decision**: Use regex-based PII detection for Vietnamese contract data.

**Rationale**:
- Fast, no external dependencies
- Vietnamese PII patterns are well-defined (CCCD format, phone format, etc.)
- Can be improved later with NER model if needed

**Alternatives considered**:
- spaCy NER: Requires Vietnamese model training
- LLM-based: Slow, costly, overkill for structured PII

### 3. Reversible PII Redaction

**Decision**: Store both `raw_text` and `redacted_text` with `pii_map` for reversible redaction.

**Rationale**:
- `redacted_text` safe for LLM processing
- `pii_map` allows authorized access to original data
- Compliant with data protection requirements

### 4. Output Format: Markdown

**Decision**: Output Markdown instead of plain text.

**Rationale**:
- Preserves document structure (headings, tables, lists)
- T4.2 (clause extraction) benefits from structure
- Tables preserved as HTML within Markdown

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| MinerU Vietnamese OCR quality | Test with sample contracts; fallback to Tesseract if needed |
| Regex PII false positives | Tune patterns with real contract samples; add context-based filtering |
| MinerU dependency size | MinerU requires ML models; consider Docker deployment |
| Large PDF performance | MinerU has sliding-window optimization; test with 100+ page contracts |
