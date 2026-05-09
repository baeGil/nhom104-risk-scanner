## Why

Task T4.1 (Contract Parser) is the entry point for the Contract Review Pipeline. The current spec calls for PyMuPDF + python-docx + Tesseract OCR, but MinerU (Apache 2.0) provides a more robust, unified solution with built-in Vietnamese OCR, auto header/footer removal, and structured Markdown output. Additionally, PII detection/redaction is needed to protect sensitive contract data before LLM processing.

## What Changes

- Replace PyMuPDF + python-docx + Tesseract with MinerU for contract document parsing
- Add PII detection and redaction layer for Vietnamese contract data
- Output structured Markdown instead of raw text (benefits downstream T4.2 clause extraction)
- Introduce `pii_map` for reversible PII redaction

## Capabilities

### New Capabilities
- `contract-parser`: Parse PDF/DOCX/TXT contracts to Markdown using MinerU, with PII detection and redaction for Vietnamese contracts

### Modified Capabilities
- `contract-review-pipeline`: Update T4.1 spec to use MinerU instead of PyMuPDF + Tesseract; add PII redaction requirement

## Impact

- `src/contract/` — new module for contract parsing
- `openspec/specs/contract-review-pipeline/spec.md` — T4.1 spec update
- Dependencies: add `mineru` package
- Downstream T4.2 benefits from structured Markdown output (easier clause boundary detection)
