-- =============================================================================
-- PhapLy Chat Persistence Smoke Check
-- =============================================================================
-- Run this in Supabase SQL Editor after 006_chat_messages.sql.
-- =============================================================================

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('chat_conversations', 'chat_messages')
ORDER BY table_name;

SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('chat_conversations', 'chat_messages')
ORDER BY table_name, ordinal_position;

SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('chat_conversations', 'chat_messages')
ORDER BY tablename, indexname;
