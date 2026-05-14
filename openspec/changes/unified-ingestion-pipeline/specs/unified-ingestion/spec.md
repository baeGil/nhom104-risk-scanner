## ADDED Requirements

### Requirement: Unified Ingestion Orchestration
The system SHALL orchestrate document ingestion through a 4-stage unified pipeline (Shell Ingestion, Preamble Scan, Segmentation, Cross-Reference Extraction).

#### Scenario: End-to-end document processing
- **WHEN** the unified pipeline script is executed
- **THEN** each document is processed sequentially through all four stages without intermediate static file dependencies.

### Requirement: Filter Core Legal Documents
The system SHALL only ingest documents where `loai_van_ban` is 'Thông tư', 'Nghị định', 'Luật', or 'Bộ luật', AND `ngay_ban_hanh` is on or after January 1, 2000.

#### Scenario: Filtering old or non-core documents
- **WHEN** a document is of type 'Chỉ thị' or was issued in 1998
- **THEN** the system skips ingestion for this document.
