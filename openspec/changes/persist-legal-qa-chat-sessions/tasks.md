## 1. Database And Environment

- [ ] 1.1 Confirm `infra/supabase/005_chat_conversations.sql` and `infra/supabase/006_chat_messages.sql` have been applied to the target Supabase project.
- [x] 1.2 Verify `frontend/.env.local` contains the active project's Supabase URL, publishable key, service role key, Auth.js secret, and Resend key.
- [x] 1.3 Add a smoke-check query or documented manual query for confirming `chat_conversations` and `chat_messages` exist.

## 2. Backend Persistence

- [x] 2.1 Add a Supabase-backed chat persistence helper for creating, loading, listing, renaming, soft-deleting conversations, and inserting messages.
- [x] 2.2 Ensure all persistence helper methods require a trusted `user_id` from authenticated server context and never trust `user_id` from client input.
- [x] 2.3 Implement ordered message insertion with collision-safe `sequence` assignment per conversation.
- [x] 2.4 Store assistant message metadata in JSONB fields: `intents`, `provisions`, `citations`, plus `token_count`.
- [x] 2.5 Update conversation metadata after message insert using existing DB trigger behavior and explicit title updates when needed.

## 3. QA API Routes

- [x] 3.1 Extend chat request/response models to accept `tabId` and return `conversationId` when a conversation is created.
- [x] 3.2 Replace in-memory conversation creation in `/api/qa/chat` with Supabase conversation creation on the first message.
- [x] 3.3 Persist the user message before or during QA processing and persist the assistant message after answer/citation metadata is complete.
- [x] 3.4 Update `/api/qa/conversations` list endpoint to return non-deleted user conversations sorted by `last_message_at`.
- [x] 3.5 Add `GET /api/qa/conversations/{id}` to load ordered messages for a user-owned active conversation.
- [x] 3.6 Add `PATCH /api/qa/conversations/{id}` to manually rename a user-owned active conversation.
- [x] 3.7 Update `DELETE /api/qa/conversations/{id}` to set `deleted_at` instead of deleting rows.
- [x] 3.8 Add best-effort AI title generation after the first completed turn with fallback to the first user message.

## 4. Frontend Legal QA

- [x] 4.1 Add a tab-scoped `tab_id` utility using `sessionStorage`.
- [x] 4.2 Update the QA API client to send `tabId`, handle streamed `conversationId`, load conversation messages, rename conversations, and soft-delete conversations.
- [x] 4.3 Update the Legal QA page to delay conversation creation until the first message.
- [x] 4.4 Restore the active tab conversation after refresh by loading messages for the stored tab conversation.
- [x] 4.5 Add conversation history loading sorted by last message time.
- [x] 4.6 Add UI support for loading prior conversations, renaming titles, and deleting conversations.
- [x] 4.7 Ensure loaded messages render persisted `intents`, `provisions`, and `citations` in existing chat bubble components.

## 5. Verification

- [ ] 5.1 Test registration/login against the developer-owned Supabase project.
- [ ] 5.2 Test first message creates one `chat_conversations` row and two `chat_messages` rows for the authenticated user.
- [ ] 5.3 Test refresh restores the same tab conversation.
- [ ] 5.4 Test opening a new tab creates a separate conversation after its first message.
- [ ] 5.5 Test conversation list ordering by `last_message_at`.
- [ ] 5.6 Test delete hides a conversation without removing its messages.
- [x] 5.7 Run relevant frontend and backend tests or document why they cannot be run locally. Python compile and TypeScript checks pass; Next build is blocked by Google Fonts network fetch in this environment.
