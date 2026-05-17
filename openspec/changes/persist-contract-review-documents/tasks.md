## 1. Database And Storage

- [x] 1.1 Create a Supabase migration for `contract_documents`, `contract_document_versions`, `contract_review_runs`, and `contract_review_snapshots`.
- [x] 1.2 Add constraints and indexes for user history, active document/version lookup, one active run per version, and one snapshot per run.
- [x] 1.3 Add SQL comments or migration notes explaining that this document-centric model supersedes the old `contract_jobs` aggregate root.
- [x] 1.4 Add a Supabase Storage bucket setup note or SQL/storage policy notes for contract source files.
- [x] 1.5 Add a verification SQL script that checks document/version/run/snapshot relationships, soft delete filtering, and ownership columns.

## 2. Backend Persistence Layer

- [x] 2.1 Add a Contract Review persistence helper for Supabase REST/PostgREST operations.
- [x] 2.2 Add file upload support to Supabase Storage and return stable `storage_path` values for contract versions.
- [x] 2.3 Implement create-document, create-version, create-run, update-run-status, save-snapshot, get-run, list-runs, and soft-delete-document operations.
- [x] 2.4 Ensure every persistence method requires backend-derived `user_id` and filters reads/writes by owner.
- [x] 2.5 Add serialization helpers so pipeline output can be saved as the frontend restore snapshot.

## 3. Backend API

- [x] 3.1 Require and validate the backend Bearer token for Contract Review upload, status, history, and delete routes.
- [x] 3.2 Update `POST /api/contracts/upload` to create a document, version, run, upload the source file, and return run identifiers.
- [x] 3.3 Update async processing to persist final run status and save the review snapshot on completion.
- [x] 3.4 Persist failed run status and error messages when parsing or review pipeline execution fails.
- [x] 3.5 Update `GET /api/contracts/{jobId}/status` to resolve `jobId` as a persisted run ID and include snapshot data for completed runs.
- [x] 3.6 Update `GET /api/contracts/history` to return persisted user-owned run summaries sorted by newest first.
- [x] 3.7 Add an authenticated document soft-delete endpoint and hide deleted documents from history/status reads.
- [x] 3.8 Keep compatibility mapping for frontend fields that still call the identifier `jobId` while internally using run IDs.

## 4. Frontend API And State

- [x] 4.1 Update `frontend/src/lib/api-contract.ts` types to include `documentId`, `versionId`, run-backed `jobId`, and snapshot-backed result fields.
- [x] 4.2 Send the backend token on contract upload requests, matching the existing Legal QA auth pattern.
- [x] 4.3 Update status polling to restore clauses, matches, compliance, and citations from completed run snapshots.
- [x] 4.4 Update history loading to use persisted run summaries and handle soft-deleted documents disappearing from history.
- [x] 4.5 Add API support for soft-deleting a contract document from the UI.

## 5. Frontend UI

- [x] 5.1 Update the Contract Review page to treat uploaded files as persisted review runs instead of transient jobs.
- [x] 5.2 Restore completed results after refresh or history navigation using the backend snapshot payload.
- [x] 5.3 Add loading and recoverable error states for missing or failed snapshots.
- [x] 5.4 Update history UI labels to use original filenames and persisted run dates.
- [x] 5.5 Wire any dashboard recent-contract entries to persisted review runs rather than mock contract data.
- [x] 5.6 Add a soft-delete action for persisted contract documents if the current UI surface supports deletion.

## 6. Verification

- [x] 6.1 Run Python compile checks for `infra/api` and related config/auth modules.
- [x] 6.2 Run frontend TypeScript checks with `npx tsc --noEmit`.
- [ ] 6.3 Apply the migration to the developer Supabase project and run the verification SQL.
- [ ] 6.4 Upload a valid contract and confirm one document, one version, one run, one storage object, and one snapshot are created.
- [ ] 6.5 Refresh or reopen a completed run and confirm the UI restores from the snapshot without re-running analysis.
- [ ] 6.6 Upload an invalid file type and confirm no document, version, run, or storage object is created.
- [ ] 6.7 Soft-delete a document and confirm it disappears from history while rows and storage files remain.
- [ ] 6.8 Confirm one user cannot access another user's persisted contract review data.
