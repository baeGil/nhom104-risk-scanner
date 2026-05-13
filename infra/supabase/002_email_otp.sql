-- =============================================================================
-- PhápLý Email OTP Schema — Supabase Migrations
-- =============================================================================
-- Run this in Supabase SQL Editor after 001_auth_schema.sql.
-- =============================================================================

-- ── email_otp_codes ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS email_otp_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash VARCHAR(255) NOT NULL,
    expires TIMESTAMPTZ NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT false,
    failed_count INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    resend_count INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    last_ip INET,
    last_user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_otp_codes_user_id ON email_otp_codes(user_id, is_used, expires);
CREATE INDEX idx_otp_codes_code_hash ON email_otp_codes(code_hash, is_used, expires);

-- ── ip_rate_limits ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ip_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address INET NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    window_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    window_duration INTERVAL NOT NULL DEFAULT INTERVAL '1 hour',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(ip_address, action_type, window_start)
);

CREATE INDEX idx_rate_limits_ip_action ON ip_rate_limits(ip_address, action_type);
CREATE INDEX idx_rate_limits_window ON ip_rate_limits(window_start);

-- ── Updated_at trigger for email_otp_codes ──────────────────────────────────

CREATE TRIGGER set_email_otp_codes_updated_at
    BEFORE UPDATE ON email_otp_codes
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

-- ── RLS Policies ────────────────────────────────────────────────────────────

ALTER TABLE email_otp_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_rate_limits ENABLE ROW LEVEL SECURITY;

-- Allow all reads/writes via service role (development mode)
CREATE POLICY "Allow all on email_otp_codes" ON email_otp_codes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on ip_rate_limits" ON ip_rate_limits FOR ALL USING (true) WITH CHECK (true);
