## MODIFIED Requirements

### Requirement: Contract upload endpoint
The system SHALL provide a POST /api/contracts/upload endpoint that accepts multipart/form-data with a file field. The endpoint SHALL validate file type (PDF, DOCX, TXT, MD) and size (max 10MB), require an authenticated backend token, create a persisted contract document, create version `1` for the uploaded file, store the file in Supabase Storage, initiate async processing, and return identifiers for the created document, version, and review run.

#### Scenario: Upload valid contract
- **WHEN** an authenticated client uploads a PDF file
- **THEN** the system stores the file, creates document/version/run records, and returns the run identifier for async processing

#### Scenario: Reject invalid file type
- **WHEN** an authenticated client uploads a PNG file
- **THEN** system returns 400 with error message

#### Scenario: Reject unauthenticated upload
- **WHEN** a client uploads a contract without a valid backend token
- **THEN** the system returns 401 and creates no persisted document, version, run, or file

### Requirement: Contract job status endpoint
The system SHALL provide a GET /api/contracts/{jobId}/status endpoint for compatibility where `jobId` maps to a persisted review run ID. The response SHALL include run status, filename, createdAt, documentId, versionId, and the saved result snapshot when the run is completed. Status values SHALL be: "uploading", "parsing", "extracting", "retrieving", "analyzing", "verifying", "completed", "failed".

#### Scenario: Check job progress
- **WHEN** an authenticated client GETs /api/contracts/run_001/status for a run they own
- **THEN** system returns the current persisted run status and metadata

#### Scenario: Completed run includes snapshot payload
- **WHEN** an authenticated client checks a completed run they own
- **THEN** the system returns the clauses, matches, compliance, citations, and other result data from the saved snapshot

#### Scenario: Reject access to another user's run
- **WHEN** an authenticated client requests status for another user's run
- **THEN** the system returns not found or unauthorized without exposing run metadata

### Requirement: Contract job history endpoint
The system SHALL provide GET /api/contracts/history returning persisted review run summaries for the authenticated user, sorted by createdAt descending, excluding runs whose parent document is soft-deleted.

#### Scenario: Get job history
- **WHEN** an authenticated client GETs /api/contracts/history
- **THEN** system returns that user's persisted review runs sorted by date

#### Scenario: Exclude soft-deleted documents from history
- **WHEN** a review run belongs to a soft-deleted document
- **THEN** the history endpoint does not include that run

## ADDED Requirements

### Requirement: Contract document delete endpoint
The system SHALL provide an authenticated endpoint to soft-delete a contract document owned by the current user.

#### Scenario: Delete own document
- **WHEN** an authenticated user deletes a contract document they own
- **THEN** the system sets `deleted_at` on the document and hides its runs from normal history

#### Scenario: Delete another user's document
- **WHEN** an authenticated user attempts to delete another user's contract document
- **THEN** the system returns not found or unauthorized and does not modify the document
