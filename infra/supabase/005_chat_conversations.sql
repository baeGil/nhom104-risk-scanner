-- =============================================================================
-- PhapLy Chat Conversations Persistence
-- =============================================================================
-- Run this in Supabase SQL Editor after 004_contract_review_persistence.sql.
-- =============================================================================

CREATE TABLE IF NOT EXISTS chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tab_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT 'New conversation',
    title_source TEXT NOT NULL DEFAULT 'fallback'
        CHECK (title_source IN ('ai', 'manual', 'fallback')),
    message_count INTEGER NOT NULL DEFAULT 0 CHECK (message_count >= 0),
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Backfill columns when the table already existed from an older/partial run.
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS tab_id TEXT NOT NULL DEFAULT '';
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS title TEXT NOT NULL DEFAULT 'New conversation';
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS title_source TEXT NOT NULL DEFAULT 'fallback';
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS message_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMPTZ;
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE chat_conversations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_last_message
    ON chat_conversations(user_id, last_message_at DESC NULLS LAST)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_created
    ON chat_conversations(user_id, created_at DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_chat_conversations_deleted_at
    ON chat_conversations(deleted_at)
    WHERE deleted_at IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_chat_conversations_user_tab_active
    ON chat_conversations(user_id, tab_id)
    WHERE deleted_at IS NULL;

DROP TRIGGER IF EXISTS set_chat_conversations_updated_at ON chat_conversations;
CREATE TRIGGER set_chat_conversations_updated_at
    BEFORE UPDATE ON chat_conversations
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

-- RLS is intentionally not enabled here yet. The current app uses Auth.js
-- session.user.id plus server-side Supabase service key access. Keep all API
-- reads/writes filtered by user_id until the app adopts Supabase Auth JWTs.
