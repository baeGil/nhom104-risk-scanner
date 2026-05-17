-- =============================================================================
-- PhapLy Contract Review Documents Persistence
-- =============================================================================
-- Run this in Supabase SQL Editor after 006_chat_messages.sql.
-- This document-centric model supersedes the older contract_jobs aggregate root
-- from 004_contract_review_persistence.sql for new development.
-- =============================================================================

INSERT INTO storage.buckets (id, name, public)
SELECT 'contract-review-files', 'contract-review-files', false
WHERE NOT EXISTS (
    SELECT 1 FROM storage.buckets WHERE id = 'contract-review-files'
);

CREATE TABLE IF NOT EXISTS contract_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL DEFAULT '',
    display_name TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS original_filename TEXT NOT NULL DEFAULT '';
ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS display_name TEXT NOT NULL DEFAULT '';
ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_documents ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS contract_document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES contract_documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL DEFAULT 1 CHECK (version_number >= 1),
    source_type TEXT NOT NULL DEFAULT 'original_upload'
        CHECK (source_type IN ('original_upload', 'ai_rewrite', 'manual_upload')),
    parent_version_id UUID REFERENCES contract_document_versions(id) ON DELETE SET NULL,
    source_run_id UUID,
    filename TEXT NOT NULL DEFAULT '',
    content_type TEXT,
    source_format TEXT NOT NULL DEFAULT 'unknown',
    file_size_bytes BIGINT NOT NULL DEFAULT 0 CHECK (file_size_bytes >= 0),
    storage_path TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS document_id UUID REFERENCES contract_documents(id) ON DELETE CASCADE;
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1;
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS source_type TEXT NOT NULL DEFAULT 'original_upload';
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS parent_version_id UUID REFERENCES contract_document_versions(id) ON DELETE SET NULL;
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS source_run_id UUID;
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS filename TEXT NOT NULL DEFAULT '';
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS content_type TEXT;
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS source_format TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT NOT NULL DEFAULT 0;
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS storage_path TEXT NOT NULL DEFAULT '';
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_document_versions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS contract_review_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES contract_documents(id) ON DELETE CASCADE,
    version_id UUID NOT NULL REFERENCES contract_document_versions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'uploading'
        CHECK (status IN ('uploading', 'parsing', 'extracting', 'retrieving', 'analyzing', 'verifying', 'completed', 'failed')),
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS document_id UUID REFERENCES contract_documents(id) ON DELETE CASCADE;
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS version_id UUID REFERENCES contract_document_versions(id) ON DELETE CASCADE;
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'uploading';
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS progress INTEGER NOT NULL DEFAULT 0;
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS error TEXT;
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_review_runs ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS contract_review_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES contract_review_runs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
    result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE contract_review_snapshots ADD COLUMN IF NOT EXISTS run_id UUID REFERENCES contract_review_runs(id) ON DELETE CASCADE;
ALTER TABLE contract_review_snapshots ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE contract_review_snapshots ADD COLUMN IF NOT EXISTS schema_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE contract_review_snapshots ADD COLUMN IF NOT EXISTS result_json JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE contract_review_snapshots ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_review_snapshots ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'contract_document_versions_source_run_id_fkey'
          AND table_name = 'contract_document_versions'
    ) THEN
        ALTER TABLE contract_document_versions
            ADD CONSTRAINT contract_document_versions_source_run_id_fkey
            FOREIGN KEY (source_run_id) REFERENCES contract_review_runs(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_contract_documents_user_name_active
    ON contract_documents(user_id, created_at DESC)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_contract_document_versions_document_version_active
    ON contract_document_versions(document_id, version_number)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_contract_document_versions_user_created_active
    ON contract_document_versions(user_id, created_at DESC)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_contract_review_runs_version_active
    ON contract_review_runs(version_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_contract_review_runs_user_created_active
    ON contract_review_runs(user_id, created_at DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_contract_review_runs_document_created_active
    ON contract_review_runs(document_id, created_at DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_contract_review_runs_status_active
    ON contract_review_runs(status)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_contract_review_snapshots_run
    ON contract_review_snapshots(run_id);

DROP TRIGGER IF EXISTS set_contract_documents_updated_at ON contract_documents;
CREATE TRIGGER set_contract_documents_updated_at
    BEFORE UPDATE ON contract_documents
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

DROP TRIGGER IF EXISTS set_contract_document_versions_updated_at ON contract_document_versions;
CREATE TRIGGER set_contract_document_versions_updated_at
    BEFORE UPDATE ON contract_document_versions
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

DROP TRIGGER IF EXISTS set_contract_review_runs_updated_at ON contract_review_runs;
CREATE TRIGGER set_contract_review_runs_updated_at
    BEFORE UPDATE ON contract_review_runs
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

DROP TRIGGER IF EXISTS set_contract_review_snapshots_updated_at ON contract_review_snapshots;
CREATE TRIGGER set_contract_review_snapshots_updated_at
    BEFORE UPDATE ON contract_review_snapshots
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

COMMENT ON TABLE contract_documents IS
    'Long-lived user-owned contract identity for Contract Review. Supersedes job-centric persistence from 004.';
COMMENT ON TABLE contract_document_versions IS
    'Stored file artifacts for contract documents, including original upload and future revised files.';
COMMENT ON TABLE contract_review_runs IS
    'One analysis execution per file version. Frontend compatibility may still call this identifier jobId.';
COMMENT ON TABLE contract_review_snapshots IS
    'Full UI restore snapshots for completed contract review runs.';

-- Storage access currently uses the Supabase service role key from FastAPI.
-- Do not enable RLS for these tables until the app moves to Supabase Auth JWTs
-- end-to-end instead of the current Auth.js backend token bridge.
