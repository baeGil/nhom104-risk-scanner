## 1. Setup

- [x] 1.1 Create `src/contract/` module structure (`__init__.py`, `models.py`, `parser.py`, `pii.py`)
- [x] 1.2 Add `mineru` and `pydantic` to project dependencies
- [x] 1.3 Install MinerU and verify Vietnamese OCR support

## 2. Contract Models

- [x] 2.1 Define `Contract` dataclass with fields: id, raw_text, redacted_text, source_format, upload_date, pii_map
- [x] 2.2 Define `ParseError` exception class with error details

## 3. PII Detection Layer

- [x] 3.1 Implement regex patterns for Vietnamese PII (CCCD, MST, phone, email, address, bank account)
- [x] 3.2 Implement `detect_pii(text)` function returning list of PII matches with type and position
- [x] 3.3 Implement `redact_pii(text, pii_matches)` function returning redacted text and pii_map
- [x] 3.4 Implement `reconstruct_text(redacted_text, pii_map)` function for reversible redaction

## 4. Contract Parser (T4.1 Core)

- [x] 4.1 Implement `ContractParser` class with `parse(file_path)` method
- [x] 4.2 Integrate MinerU for PDF/DOCX/TXT → Markdown conversion
- [x] 4.3 Implement format detection (PDF text vs scanned, DOCX, TXT)
- [x] 4.4 Chain parser output through PII detection/redaction
- [x] 4.5 Return `Contract` object with all fields populated
- [x] 5.1 Handle corrupted files with descriptive error messages
- [x] 5.2 Handle unsupported formats with clear exception
- [x] 5.3 Handle MinerU OCR failures gracefully

## 6. Tests

- [x] 6.1 Create `src/contract/tests/` directory with test structure
- [x] 6.2 Write unit tests for PII detection patterns
- [x] 6.3 Write unit tests for PII redaction/reconstruction
- [x] 6.4 Write integration tests for ContractParser with sample files
- [x] 6.5 Write error handling tests (corrupted files, unsupported formats)
