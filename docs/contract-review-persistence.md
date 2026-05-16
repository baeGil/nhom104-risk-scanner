# Contract Review Persistence

Initial implementation uses a backend-local JSON repository at `output/contract_jobs.json`.

This is intentionally wrapped behind `infra.api.job_store.JobStore` so the storage backend can be replaced by Supabase/Postgres without changing contract processing or frontend API shapes.

Persisted job fields:

- job metadata: `job_id`, `filename`, `status`, `progress`, `created_at`, `error`
- extracted `clauses`
- legal `matches`
- aggregate `compliance`
- citation `citations`

Neo4j remains the legal knowledge graph. User-uploaded contract content and review results are application data and should not be stored as legal graph nodes.

Production migration target: Supabase/Postgres tables for contract jobs, clauses, matches, compliance results, and citation verification results.
