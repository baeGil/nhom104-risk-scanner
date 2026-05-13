-- =============================================================================
-- PhápLý Auth Schema — Supabase Migrations
-- =============================================================================
-- Run this in Supabase SQL Editor.
-- =============================================================================

-- ── users table (public schema, for Auth.js) ─────────────────────────────────
-- Note: This is separate from Supabase Auth (auth.users).
-- We use this table to store user profile data and link to auth.users.

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    email_verified TIMESTAMPTZ,
    image TEXT,
    password_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── user_roles ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'free' CHECK (role IN ('free', 'premium', 'admin')),
    subscription_tier VARCHAR(50),
    subscription_status VARCHAR(50),
    subscription_ends_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── password_reset_tokens ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);

-- ── usage_counters ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS usage_counters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    period_start DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL DEFAULT 'monthly',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, resource_type, period_start, period_type)
);

CREATE INDEX idx_usage_counters_user_resource ON usage_counters(user_id, resource_type, period_start);

-- ── Updated_at triggers ──────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

CREATE TRIGGER set_user_roles_updated_at
    BEFORE UPDATE ON user_roles
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

CREATE TRIGGER set_usage_counters_updated_at
    BEFORE UPDATE ON usage_counters
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

-- ── RLS Policies ─────────────────────────────────────────────────────────────
-- Note: Service role key bypasses RLS. These policies are for client-side access.

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_reset_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_counters ENABLE ROW LEVEL SECURITY;

-- Allow all reads/writes via service role (development mode)
-- In production, replace with proper user-scoped policies
CREATE POLICY "Allow all on users" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on user_roles" ON user_roles FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on password_reset_tokens" ON password_reset_tokens FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on usage_counters" ON usage_counters FOR ALL USING (true) WITH CHECK (true);
