## ADDED Requirements

### Requirement: Contract documents persist as long-lived user-owned records
The system SHALL persist each uploaded contract as a long-lived `contract_documents` record owned by the authenticated user. A document SHALL include a stable ID, `user_id`, original filename, display name equal to the original filename by default, timestamps, and nullable `deleted_at`.

#### Scenario: Create document for upload
- **WHEN** an authenticated user uploads a supported contract file
- **THEN** the system creates a `contract_documents` row owned by that user before or during review processing

#### Scenario: Hide soft-deleted document
- **WHEN** a document has `deleted_at` set
- **THEN** normal document, version, run, and history queries exclude it

### Requirement: Contract file versions persist storage-backed artifacts
The system SHALL persist each concrete contract file as a `contract_document_versions` record linked to a document. Each version SHALL include `document_id`, `user_id`, `version_number`, `source_type`, filename, content type, file size, storage path, timestamps, and nullable `deleted_at`.

#### Scenario: Store original upload as version one
- **WHEN** a user uploads a new contract file
- **THEN** the system stores the file in Supabase Storage and creates version `1` with `source_type="original_upload"`

#### Scenario: Preserve future rewrite lineage
- **WHEN** a later version is created from a previous version or review run
- **THEN** the version records its `parent_version_id` and/or `source_run_id`

### Requirement: Each contract version has one review run
The system SHALL persist each analysis execution as a `contract_review_runs` record linked to exactly one document version. A non-deleted version SHALL have at most one active review run.

#### Scenario: Create run for version
- **WHEN** the system starts review processing for a contract version
- **THEN** it creates a run with `document_id`, `version_id`, `user_id`, `status`, and `started_at`

#### Scenario: Prevent duplicate run for version
- **WHEN** a review run already exists for an active version
- **THEN** the system does not create a second active run for that version

### Requirement: Review snapshots restore full result UI
The system SHALL persist one `contract_review_snapshots` row per completed review run. The snapshot SHALL include `run_id`, `user_id`, `schema_version`, and `result_json` containing the full Contract Review result payload required by the frontend.

#### Scenario: Save snapshot after successful review
- **WHEN** a contract review pipeline completes successfully
- **THEN** the system stores the serialized review result in `contract_review_snapshots.result_json`

#### Scenario: Restore completed review from snapshot
- **WHEN** a user opens a completed review run from history
- **THEN** the system returns the saved snapshot payload without re-running the review pipeline

### Requirement: Contract review persistence is user-scoped by backend ownership checks
The system SHALL derive `user_id` from the authenticated backend token for every Contract Review persistence operation. The client MUST NOT be trusted to provide or override `user_id`.

#### Scenario: User reads own run
- **WHEN** an authenticated user requests a review run they own
- **THEN** the system returns the run and snapshot

#### Scenario: User cannot read another user's run
- **WHEN** an authenticated user requests a review run owned by another user
- **THEN** the system returns not found or unauthorized without exposing the run data

### Requirement: Soft delete retains stored files and snapshots
The system SHALL soft-delete contract documents by setting `contract_documents.deleted_at`. Soft delete SHALL hide the document and its runs from normal history while retaining database rows and Supabase Storage files.

#### Scenario: Soft delete document
- **WHEN** a user deletes a contract document
- **THEN** the system sets `deleted_at` and excludes the document from normal history

#### Scenario: Retain storage file after soft delete
- **WHEN** a document is soft-deleted
- **THEN** the system does not delete the associated Supabase Storage files as part of the user-facing delete operation
