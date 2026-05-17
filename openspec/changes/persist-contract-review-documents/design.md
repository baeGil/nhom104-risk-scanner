## Context

Contract Review currently exposes an async job model through `/api/contracts/upload`, `/api/contracts/{job_id}/status`, and `/api/contracts/history`. Runtime state is still centered on `infra/api/job_store.py`, while `infra/supabase/004_contract_review_persistence.sql` models persistence as `contract_jobs` plus job-scoped detail tables. That model is useful for a single analysis run, but it does not represent a long-lived contract document, file revisions, AI-rewritten files, or a full UI restore snapshot.

The target product model is document-centric:

- A user owns long-lived contract documents.
- Each document has one or more file versions.
- Each file version is reviewed once.
- Each review run has a snapshot that can restore the whole result UI.
- Original, manually uploaded, and future AI-rewritten files are stored in Supabase Storage.
- Deleting a document is a soft delete in the database; the stored files remain for recovery/audit unless a future cleanup job removes them.

Auth should stay aligned with Legal QA persistence: the frontend obtains a backend token from Auth.js, FastAPI validates it, derives `user_id`, and applies user filters server-side.

## Goals / Non-Goals

**Goals:**

- Persist Contract Review documents, file versions, review runs, and result snapshots in Supabase.
- Store original uploaded files in Supabase Storage and reference them from file-version rows.
- Restore completed Contract Review result pages entirely from a saved snapshot.
- List history by review run, including status, filename, run date, and document/version identifiers.
- Soft-delete documents and hide their versions/runs from normal user history.
- Preserve enough version lineage to support future AI rewrite flows.
- Use backend-enforced ownership checks consistent with Legal QA.

**Non-Goals:**

- Implement AI contract rewriting in this change.
- Implement multiple review runs for a single file version; one version has one run.
- Implement analytics/search across clauses, matches, or citations.
- Implement Legal QA conversation linking for contract runs now.
- Hard-delete files from Supabase Storage when a document is soft-deleted.
- Adopt Supabase Auth JWT/RLS for Contract Review persistence in this change.

## Decisions

### Use document/version/run/snapshot tables

The schema will introduce:

- `contract_documents`: long-lived user-owned contract identity.
- `contract_document_versions`: one stored file artifact for a document.
- `contract_review_runs`: one analysis execution for one version.
- `contract_review_snapshots`: one JSONB payload for restoring the full UI for a run.

Alternative considered: extend `contract_jobs` with more fields. This keeps the current table but overloads one row with document identity, file artifact metadata, and execution state. That makes AI-rewritten files and version lineage harder to reason about.

### Store file metadata on versions, not runs

`filename`, `content_type`, `file_size_bytes`, and `storage_path` belong to `contract_document_versions`. A run consumes a version; it should not own the file identity.

Alternative considered: keep `storage_path` on the run. This works for the first upload but breaks down when later versions are created from AI rewrite or manual upload.

### Treat each version as reviewable once

`contract_review_runs.version_id` should have an active unique constraint. If the user uploads a new file or accepts an AI rewrite, the system creates a new version and then a new run.

Alternative considered: allow many runs on one version. That is more flexible but adds ambiguity around which run is canonical for a version. The current product requirement is one run per version.

### Use snapshots as the restore source of truth

`contract_review_snapshots.result_json` stores the full response shape needed by the frontend to restore the Contract Review result screen. This is the primary read path for reopening completed reviews.

Alternative considered: normalize every clause, match, citation, and compliance item immediately. That supports future analytics but adds joins and mapping work before there is a product need. Normalized detail tables can be added later using `run_id` as the parent.

### Preserve version lineage for future AI rewrite

`contract_document_versions` should include `source_type`, `parent_version_id`, and optionally `source_run_id`. Initial uploads use `source_type='original_upload'`; future AI rewrites can use `source_type='ai_rewrite'`; user-supplied revised files can use `source_type='manual_upload'`.

Alternative considered: defer lineage fields until AI rewrite is implemented. Adding them now keeps the persistence model stable and avoids a migration when the rewrite feature arrives.

### Use backend token ownership checks

Contract Review persistence should use the same auth bridge as Legal QA. The client sends a Bearer token from `/api/auth/backend-token`; FastAPI derives `user_id`; all reads/writes are filtered by that `user_id`.

Alternative considered: keep the current RLS policies in `004_contract_review_persistence.sql`. That is viable with Supabase Auth JWTs, but the current app auth boundary is Auth.js plus backend-token validation, so backend-enforced ownership keeps the architecture consistent.

## Risks / Trade-offs

- JSONB snapshots are harder to query deeply -> Accept this for the current restore-first requirement; add run-scoped normalized tables later if analytics/search becomes necessary.
- Supabase Storage files remain after soft delete -> This supports recovery and audit, but storage usage can grow; add an admin cleanup workflow later if needed.
- Existing frontend types use `jobId` -> Keep API response compatibility where practical during migration, but internally map jobs to `runId`.
- Current in-memory job store cannot survive backend restarts -> Persist run status and snapshot in Supabase, and use in-memory state only as a transient processing helper if needed.
- RLS mismatch with existing `004` migration -> Supersede the old job-centric migration for new development and document that ownership is enforced by FastAPI until the app adopts Supabase Auth JWTs.

## Migration Plan

1. Add a new Supabase migration that creates document/version/run/snapshot tables and required indexes.
2. Configure or document a Supabase Storage bucket for contract files.
3. Implement a Contract Review persistence helper for Supabase REST/PostgREST and Storage operations.
4. Update upload flow to create document, version, run, upload the file, and start async review processing.
5. Update processing completion to save the full snapshot and mark the run `completed` or `failed`.
6. Update status/history endpoints to read persisted runs and snapshots by authenticated `user_id`.
7. Update frontend contract API and UI to restore completed reviews from snapshots.
8. Keep the existing pipeline behavior unchanged; only persistence and API state ownership change.
9. Validate with a real Supabase project: upload, complete review, refresh/reopen, history, and soft delete.
