## Why

Legal QA conversations are currently held in frontend state and an in-memory backend dictionary, so users lose chat history after refresh, backend restart, or switching devices. Persisting chat sessions in Supabase makes the Legal QA tab usable as a real logged-in product feature and lets each authenticated user own their conversation history.

## What Changes

- Persist Legal QA conversations in Supabase using `chat_conversations` rows owned by `users.id`.
- Persist every user and assistant message in `chat_messages`, including content, role, token count, intents, provisions, and citations.
- Use a browser-tab identifier so each browser tab maps to its own active conversation while refresh restores that tab's conversation.
- Delay conversation creation until the user sends the first message.
- Generate an AI-backed conversation title after the first turn and allow manual title updates later.
- Soft-delete conversations by setting `deleted_at`, hiding them from normal history without deleting message rows.
- Replace in-memory conversation CRUD in the QA API with user-scoped Supabase persistence.
- Update the Legal QA frontend to restore the tab conversation after refresh, list conversations by `last_message_at`, and delete conversations via soft delete.

## Capabilities

### New Capabilities

### Modified Capabilities
- `backend-api`: QA chat and conversation endpoints persist user-scoped Legal QA conversations and messages in Supabase instead of in memory.
- `legal-qa-ui`: Legal QA UI restores the active tab conversation after refresh and manages persistent conversation history for the logged-in user.

## Impact

- Supabase schema: uses `infra/supabase/005_chat_conversations.sql` and `infra/supabase/006_chat_messages.sql`.
- Backend API: `infra/api/qa_routes.py`, API models, and any Supabase persistence helper added for conversation storage.
- Frontend: `frontend/src/app/(app)/legal-qa/page.tsx`, QA API client, and tab-scoped `sessionStorage` conversation tracking.
- Auth boundary: all chat persistence is scoped by authenticated `session.user.id`; client-provided `user_id` is never trusted.
- Testing: backend API persistence tests and frontend behavior checks for refresh, new tab, listing, and soft delete.
