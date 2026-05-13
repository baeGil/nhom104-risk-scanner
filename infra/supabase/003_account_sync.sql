-- =============================================================================
-- PhápLý Account Sync Migration
-- =============================================================================
-- Run this in Supabase SQL Editor after 002_email_otp.sql.
-- =============================================================================

-- ── Add linked_providers column ─────────────────────────────────────────────

ALTER TABLE users ADD COLUMN IF NOT EXISTS linked_providers JSONB DEFAULT '[]';

-- ── Migrate existing users ──────────────────────────────────────────────────

-- Users with password_hash → credentials
UPDATE users SET linked_providers = '["credentials"]'
WHERE password_hash IS NOT NULL AND linked_providers = '[]';

-- Users with image from Google → google
UPDATE users SET linked_providers = '["google"]'
WHERE image IS NOT NULL AND image LIKE '%googleusercontent.com%' AND linked_providers = '[]';

-- Users with image from GitHub → github
UPDATE users SET linked_providers = '["github"]'
WHERE image IS NOT NULL AND image LIKE '%github.com%' AND linked_providers = '[]';

-- Users with no password_hash and no image → likely OAuth with no image
-- Check by email_verified pattern or other heuristics
-- For safety, leave these as [] - they'll be updated on next login
