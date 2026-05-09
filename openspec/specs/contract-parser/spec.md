## ADDED Requirements

### Requirement: Parse contract documents to Markdown
The system SHALL parse PDF, DOCX, and TXT contract documents and output structured Markdown. PDF parsing SHALL use MinerU with automatic OCR detection for scanned documents. Output SHALL preserve document structure including headings, paragraphs, tables (as HTML), and lists.

#### Scenario: Parse text-based PDF
- **WHEN** a text-based PDF contract is provided
- **THEN** the system extracts text and converts to Markdown preserving structure

#### Scenario: Parse scanned PDF
- **WHEN** a scanned PDF contract is provided
- **THEN** the system automatically detects scanning and applies OCR to extract text

#### Scenario: Parse DOCX document
- **WHEN** a DOCX contract is provided
- **THEN** the system converts to Markdown preserving structure

#### Scenario: Parse plain text
- **WHEN** a TXT file is provided
- **THEN** the system returns the text as-is with minimal cleaning

### Requirement: Detect and redact Vietnamese PII
The system SHALL detect and redact personally identifiable information (PII) from contract text. Detected PII types SHALL include: CCCD/CMND (9-12 digits), mã số thuế (10-13 digits), phone numbers (+84/0 prefix), email addresses, bank account numbers (10-16 digits with context), and Vietnamese addresses. PII SHALL be replaced with type-specific placeholders (e.g., `[REDACTED_CCCD]`, `[REDACTED_PHONE]`).

#### Scenario: Redact CCCD number
- **WHEN** contract text contains a 9-12 digit CCCD number
- **THEN** the number is replaced with `[REDACTED_CCCD]`

#### Scenario: Redact phone number
- **WHEN** contract text contains a Vietnamese phone number
- **THEN** the number is replaced with `[REDACTED_PHONE]`

#### Scenario: Redact email address
- **WHEN** contract text contains an email address
- **THEN** the email is replaced with `[REDACTED_EMAIL]`

#### Scenario: Redact tax code
- **WHEN** contract text contains a 10-13 digit tax code
- **THEN** the number is replaced with `[REDACTED_MST]`

### Requirement: Maintain reversible PII mapping
The system SHALL maintain a mapping between original PII values and their redacted placeholders. The mapping SHALL be stored separately from the redacted text and SHALL allow authorized reconstruction of original text.

#### Scenario: PII map creation
- **WHEN** PII is detected and redacted
- **THEN** a pii_map dictionary maps each placeholder to its original value

#### Scenario: Reconstruct original text
- **WHEN** given redacted_text and pii_map
- **THEN** the original text can be reconstructed by replacing placeholders

### Requirement: Return structured Contract output
The system SHALL return a Contract dataclass containing: id (UUID), raw_text (original Markdown), redacted_text (PII-redacted), source_format ("pdf" | "docx" | "txt"), upload_date (current date), and pii_map (dict of placeholder → original value).

#### Scenario: Successful parse output
- **WHEN** a contract is successfully parsed
- **THEN** a Contract object is returned with all fields populated

#### Scenario: Parse error handling
- **WHEN** parsing fails (corrupted file, unsupported format)
- **THEN** the system raises a descriptive exception with error details
