## Context

Legal QA currently stores conversation state in React component state and in an in-memory dictionary inside `infra/api/qa_routes.py`. This is enough for a mock/demo flow but loses history on page refresh, backend restart, and any move between devices. The project already stores authenticated users in Supabase `users`, and the frontend obtains the current owner through Auth.js `session.user.id`.

The Supabase schema for chat persistence is split into:

- `chat_conversations`: user-owned conversation metadata, tab mapping, title, message count, last message timestamp, and soft delete.
- `chat_messages`: ordered message history with content, role, token count, intents, provisions, citations, and metadata.

## Goals / Non-Goals

**Goals:**
- Persist each authenticated user's Legal QA conversations and messages in Supabase.
- Create a conversation only when the user sends the first message.
- Keep one active conversation per browser tab using a tab-scoped identifier stored in `sessionStorage`.
- Restore the current tab's conversation after refresh.
- Store assistant metadata needed to replay the UI: intents, provisions, citations, and token counts.
- List conversations by `last_message_at` and soft-delete conversations by setting `deleted_at`.
- Keep all writes user-scoped using the authenticated session owner.

**Non-Goals:**
- Implement full-text search over chat history.
- Implement Supabase Auth JWT-based RLS for chat tables.
- Sync a single conversation live across multiple tabs.
- Persist streamed partial tokens before the assistant response completes.
- Change the QA retrieval, intent, citation verification, or answer-generation algorithms.

## Decisions

### Use Supabase Postgres as the source of truth

The in-memory conversation dictionary will be replaced by Supabase-backed storage. `chat_conversations` owns metadata and `chat_messages` owns the turn-by-turn history.

Alternative considered: store one JSON document per conversation. This is simpler initially, but makes ordered message retrieval, token accounting, and future pagination harder.

### Use Auth.js `session.user.id` as the owner

The backend/API layer must derive `user_id` from the authenticated session or trusted backend token, not from the client request body. The client can send `conversationId` and `tabId`, but ownership checks must happen server-side.

Alternative considered: trust a `userId` parameter from the frontend. This is rejected because it would allow one user to read or write another user's conversations.

### Use `sessionStorage` for tab identity

The frontend will create a random `tab_id` per browser tab and store it in `sessionStorage`. `sessionStorage` survives refresh but is isolated from normal new tabs, matching the desired behavior: refresh resumes the same conversation, while a new tab starts a separate conversation.

Alternative considered: use `localStorage`. This would be shared across tabs and would collapse multiple tabs into the same conversation.

### Store citations, provisions, and intents as JSONB on messages

Assistant messages will keep renderable metadata directly in `chat_messages`. This avoids extra joins and preserves the shape already used by the frontend chat bubble.

Alternative considered: normalize citations and provisions into child tables. That would be useful for cross-conversation analytics, but it adds complexity not needed for the current history/restore flow.

### Soft-delete conversations only

Deleting a conversation sets `chat_conversations.deleted_at`. Messages remain available for audit and potential restore, but normal list/load endpoints exclude deleted conversations.

Alternative considered: hard delete. This is simpler, but removes recovery options and makes debugging harder.

### Generate title after the first completed turn

The title should be generated after the first user question and assistant answer are available. If title generation fails, the system falls back to a short title derived from the first user message and marks `title_source='fallback'`.

Alternative considered: generate title before answering. This adds latency before the main user-visible answer and has less context.

## Risks / Trade-offs

- Duplicate-tab behavior can copy `sessionStorage` in some browsers -> The frontend should detect first load for a duplicated tab and mint a new `tab_id` when appropriate, or accept that duplicate-tab may initially reference the same conversation until a new chat is started.
- Backend currently lives in Python while Auth.js session is in Next.js -> Implementation must choose a consistent auth bridge for QA calls, likely by using the existing backend token route or a Next.js API proxy.
- JSONB metadata is less relationally queryable than normalized tables -> Keep GIN indexes for `citations` and `provisions`; normalize later if analytics/search requirements appear.
- Message `sequence` must be collision-free under concurrent sends -> Disable sending while streaming in the frontend and compute sequence inside the persistence layer from the current conversation max sequence.
- Title generation adds an LLM call -> Make title generation best-effort and never block saving the conversation/messages.

## Migration Plan

1. Apply `infra/supabase/005_chat_conversations.sql` after contract persistence.
2. Apply `infra/supabase/006_chat_messages.sql` after conversations.
3. Implement persistence helpers and update QA API routes to read/write Supabase.
4. Update frontend QA client and page state to use `tab_id`, restore conversation history, and display persisted metadata.
5. Verify registration/auth uses the developer's own Supabase project and that chat rows are created with the logged-in `users.id`.
6. Rollback code by switching the QA route back to in-memory storage if needed; schema rollback should be handled manually only for development projects because it drops persisted history.

## Open Questions

- Should the Python FastAPI service validate Auth.js sessions directly, or should Legal QA calls be proxied through Next.js API routes that already have `auth()` access?
- Which LLM/provider should generate conversation titles in development when API keys are not configured?
