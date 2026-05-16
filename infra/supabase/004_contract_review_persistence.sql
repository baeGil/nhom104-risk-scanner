-- =============================================================================
-- PhapLy Contract Review Persistence
-- =============================================================================
-- Run this in Supabase SQL Editor after 003_account_sync.sql.
-- =============================================================================

CREATE TABLE IF NOT EXISTS contract_jobs (
    job_id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT,
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    storage_path TEXT,
    status TEXT NOT NULL DEFAULT 'uploading'
        CHECK (status IN ('uploading', 'parsing', 'extracting', 'retrieving', 'analyzing', 'verifying', 'completed', 'failed')),
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error TEXT
);

-- Backfill columns when the table already existed from an older/partial run.
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS filename TEXT NOT NULL DEFAULT '';
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS content_type TEXT;
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT NOT NULL DEFAULT 0;
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS storage_path TEXT;
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'uploading';
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS progress INTEGER NOT NULL DEFAULT 0;
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE contract_jobs ADD COLUMN IF NOT EXISTS error TEXT;

CREATE TABLE IF NOT EXISTS contract_clauses (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES contract_jobs(job_id) ON DELETE CASCADE,
    index INTEGER NOT NULL DEFAULT 0,
    type TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    risk_level TEXT NOT NULL DEFAULT 'low'
);

CREATE TABLE IF NOT EXISTS contract_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT NOT NULL REFERENCES contract_jobs(job_id) ON DELETE CASCADE,
    clause_id TEXT REFERENCES contract_clauses(id) ON DELETE CASCADE,
    uid TEXT NOT NULL DEFAULT '',
    citation TEXT NOT NULL DEFAULT '',
    document_title TEXT NOT NULL DEFAULT '',
    segment_type TEXT NOT NULL DEFAULT '',
    score DOUBLE PRECISION NOT NULL DEFAULT 0,
    validity_signal TEXT NOT NULL DEFAULT 'latest_known',
    score_factors JSONB NOT NULL DEFAULT '{}'::jsonb,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS contract_compliance (
    job_id TEXT PRIMARY KEY REFERENCES contract_jobs(job_id) ON DELETE CASCADE,
    violations JSONB NOT NULL DEFAULT '[]'::jsonb,
    risks JSONB NOT NULL DEFAULT '[]'::jsonb,
    suggestions JSONB NOT NULL DEFAULT '[]'::jsonb,
    citations JSONB NOT NULL DEFAULT '[]'::jsonb,
    clause_results JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS contract_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT NOT NULL REFERENCES contract_jobs(job_id) ON DELETE CASCADE,
    clause_id TEXT REFERENCES contract_clauses(id) ON DELETE SET NULL,
    display_text TEXT NOT NULL DEFAULT '',
    uid TEXT NOT NULL DEFAULT '',
    verified BOOLEAN NOT NULL DEFAULT false,
    reason TEXT NOT NULL DEFAULT '',
    document_title TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_contract_jobs_user_created ON contract_jobs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contract_jobs_status ON contract_jobs(status);
CREATE INDEX IF NOT EXISTS idx_contract_clauses_job ON contract_clauses(job_id);
CREATE INDEX IF NOT EXISTS idx_contract_matches_job ON contract_matches(job_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_contract_citations_job ON contract_citations(job_id, sort_order);

DROP TRIGGER IF EXISTS set_contract_jobs_updated_at ON contract_jobs;
CREATE TRIGGER set_contract_jobs_updated_at
    BEFORE UPDATE ON contract_jobs
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE contract_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_clauses ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_compliance ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_citations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read own contract jobs" ON contract_jobs;
CREATE POLICY "Users can read own contract jobs"
    ON contract_jobs FOR SELECT USING (auth.uid() = contract_jobs.user_id);

DROP POLICY IF EXISTS "Users can read own contract clauses" ON contract_clauses;
CREATE POLICY "Users can read own contract clauses"
    ON contract_clauses FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM contract_jobs j
        WHERE j.job_id = contract_clauses.job_id AND j.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can read own contract matches" ON contract_matches;
CREATE POLICY "Users can read own contract matches"
    ON contract_matches FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM contract_jobs j
        WHERE j.job_id = contract_matches.job_id AND j.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can read own contract compliance" ON contract_compliance;
CREATE POLICY "Users can read own contract compliance"
    ON contract_compliance FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM contract_jobs j
        WHERE j.job_id = contract_compliance.job_id AND j.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS "Users can read own contract citations" ON contract_citations;
CREATE POLICY "Users can read own contract citations"
    ON contract_citations FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM contract_jobs j
        WHERE j.job_id = contract_citations.job_id AND j.user_id = auth.uid()
    ));
