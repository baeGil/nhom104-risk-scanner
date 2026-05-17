-- Verify contract review document persistence.

SELECT id, user_id, original_filename, display_name, deleted_at, created_at
FROM contract_documents
ORDER BY created_at DESC;

SELECT id, document_id, user_id, version_number, source_type, filename, source_format, storage_path, deleted_at, created_at
FROM contract_document_versions
ORDER BY created_at DESC;

SELECT id, document_id, version_id, user_id, status, progress, started_at, completed_at, error, deleted_at, created_at
FROM contract_review_runs
ORDER BY created_at DESC;

SELECT id, run_id, user_id, schema_version, jsonb_typeof(result_json) AS result_type, created_at
FROM contract_review_snapshots
ORDER BY created_at DESC;

SELECT
    d.id AS document_id,
    v.id AS version_id,
    r.id AS run_id,
    s.id AS snapshot_id,
    d.deleted_at AS document_deleted_at
FROM contract_documents d
LEFT JOIN contract_document_versions v ON v.document_id = d.id
LEFT JOIN contract_review_runs r ON r.version_id = v.id
LEFT JOIN contract_review_snapshots s ON s.run_id = r.id
ORDER BY d.created_at DESC;
