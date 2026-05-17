## Why

Contract review results currently behave like short-lived jobs: upload state and analysis output are tied to one processing job and are not modeled as long-lived user documents. The product now needs contract reviews to persist in Supabase, restore the full result UI, retain original and revised files, and support future AI rewrite flows where a revised contract version is reviewed again.

## What Changes

- Add a document-centric persistence model for Contract Review:
  - long-lived `contract_documents`
  - file-specific `contract_document_versions`
  - one review run per version in `contract_review_runs`
  - full UI restore payloads in `contract_review_snapshots`
- Store source contract files and future AI-rewritten files in Supabase Storage, referenced by document versions.
- Soft-delete contract documents using `deleted_at`; soft-deleted documents and their runs are hidden from normal history.
- Replace the current job-centric persistence contract with document/version/run/snapshot semantics while preserving async review behavior.
- Restore completed review results from a saved snapshot instead of requiring the in-memory job store.
- Keep ownership enforcement aligned with Legal QA: FastAPI derives `user_id` from the authenticated backend token and filters all Contract Review reads/writes server-side.
- Defer cross-linking Contract Review runs to Legal QA conversations, but preserve enough identifiers to support that future capability.

## Capabilities

### New Capabilities
- `contract-review-persistence`: Long-lived Supabase persistence for contract documents, file versions, review runs, snapshots, soft delete, and storage references.

### Modified Capabilities
- `backend-api`: Contract Review endpoints SHALL expose document/version/run/snapshot semantics and authenticated user-scoped persistence instead of relying on transient in-memory jobs.
- `contract-review-ui`: Contract Review history and result restore SHALL load persisted review runs and snapshots, not mock data or in-memory job data.

## Impact

- Supabase migrations: replace or supersede the current job-centric `004_contract_review_persistence.sql` model with document/version/run/snapshot tables and storage references.
- Backend API: update `infra/api/contract_routes.py` and add a persistence helper similar in role to the Legal QA chat store.
- Frontend API client: update `frontend/src/lib/api-contract.ts` to handle persisted run IDs and restored snapshots.
- Frontend UI: update `frontend/src/app/(app)/contract-review/page.tsx` and dashboard/history entry points to list persisted runs and reopen full results.
- Auth/security: reuse the existing backend token flow and server-side `user_id` checks used by Legal QA.
- Storage: configure or document a Supabase Storage bucket for original and generated contract files.
