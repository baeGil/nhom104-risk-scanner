# Persist Legal QA Chat Sessions - Handoff

## Goal

Persist Legal QA chat sessions for authenticated users using the developer's own Supabase project.

The target behavior:

- Auth user data lives in Supabase `users`.
- Each Legal QA browser tab has its own conversation.
- Refreshing the same tab restores that tab's conversation.
- Every user and assistant message is saved.
- Assistant metadata is saved with each message: `intents`, `provisions`, `citations`, and `token_count`.
- Conversations are soft-deleted by `deleted_at`.
- Conversation history appears in the left sidebar under the active `Hỏi đáp pháp lý` item, above `Cài đặt`.
- The active sidebar item has an up/down arrow to show/hide history.
- History shows about 5 items before scrolling.

## Important Context

Auth is implemented in the Next.js frontend, not in Python:

- Main Auth.js config: `frontend/src/auth.ts`
- Backend token route: `frontend/src/app/api/auth/backend-token/route.ts`
- FastAPI validates that token in `src/auth.py`

Supabase config is read from `frontend/.env.local` for frontend routes. Python config now also loads `frontend/.env.local` via `src/config.py`.

The FastAPI QA API requires a Bearer token. The frontend gets it from:

```text
GET /api/auth/backend-token
```

and sends it to:

```text
http://localhost:8000/api/qa/*
```

## Supabase Schema

Two migration files were added:

- `infra/supabase/005_chat_conversations.sql`
- `infra/supabase/006_chat_messages.sql`

Smoke-check SQL was added:

- `infra/supabase/verify_chat_persistence.sql`

Expected tables:

```text
chat_conversations
  id uuid
  user_id uuid references users(id)
  tab_id text
  title text
  title_source text
  message_count integer
  last_message_at timestamptz
  created_at timestamptz
  updated_at timestamptz
  deleted_at timestamptz

chat_messages
  id uuid
  conversation_id uuid references chat_conversations(id)
  user_id uuid references users(id)
  role text
  content text
  sequence integer
  token_count integer
  citations jsonb
  provisions jsonb
  intents jsonb
  metadata jsonb
  created_at timestamptz
  updated_at timestamptz
```

Run migrations in Supabase SQL Editor in this order:

```text
001_auth_schema.sql
002_email_otp.sql
003_account_sync.sql
004_contract_review_persistence.sql
005_chat_conversations.sql
006_chat_messages.sql
```

Then optionally run:

```text
verify_chat_persistence.sql
```

## OpenSpec Change

Change created:

```text
openspec/changes/persist-legal-qa-chat-sessions/
```

Artifacts:

- `proposal.md`
- `design.md`
- `specs/backend-api/spec.md`
- `specs/legal-qa-ui/spec.md`
- `tasks.md`

Current task progress was `23/30` after implementation. Completed tasks include DB smoke query, backend persistence helper, QA API route updates, frontend tab handling, frontend history UI, and local compile/type checks.

Remaining tasks are runtime verification against the user's real Supabase project:

- Confirm `005` and `006` are applied.
- Test registration/login.
- Test first message creates one `chat_conversations` row and two `chat_messages` rows.
- Test refresh restores same tab conversation.
- Test new tab creates separate conversation.
- Test ordering by `last_message_at`.
- Test delete hides conversation without deleting messages.

## Backend Changes

Added:

- `infra/api/chat_store.py`

This is a small Supabase REST/PostgREST client using `requests`, so no new Python dependency was needed.

It handles:

- create conversation
- get conversation by id
- get conversation by tab id
- list conversations
- list messages
- insert messages with ordered `sequence`
- rename conversation
- soft-delete conversation
- estimate token count

Modified:

- `infra/api/qa_routes.py`
- `infra/api/models.py`
- `infra/api/sse.py`
- `src/config.py`

Behavior:

- `POST /api/qa/chat` now accepts `tabId`.
- If `conversationId` is absent, backend creates a Supabase conversation for that `tabId`.
- The SSE stream sends `conversationId` in the first chunk.
- User message is persisted.
- Assistant message is persisted with `intents`, `provisions`, `citations`, and `token_count`.
- Conversation title is generated best-effort using OpenAI if configured; fallback uses the first user message.
- `GET /api/qa/conversations` lists non-deleted conversations sorted by `last_message_at`.
- `GET /api/qa/conversations/{id}` loads messages.
- `GET /api/qa/conversations/tab/{tab_id}` restores the active tab conversation.
- `PATCH /api/qa/conversations/{id}` renames.
- `DELETE /api/qa/conversations/{id}` sets `deleted_at`.

## Frontend Changes

Added:

- `frontend/src/lib/chat-tab.ts`

This manages tab-specific IDs in `sessionStorage`.

Modified:

- `frontend/src/lib/api-client.ts`
- `frontend/src/lib/api-qa.ts`
- `frontend/src/lib/mock-api-qa.ts`
- `frontend/src/components/qa/chat-bubble.tsx`
- `frontend/src/app/(app)/legal-qa/page.tsx`
- `frontend/src/components/layout/sidebar.tsx`
- `frontend/src/app/api/auth/backend-token/route.ts`
- `frontend/src/app/api/auth/auto-login/route.ts`

Important auth fix:

`jose` expiration was incorrect before:

```ts
.setExpirationTime(15 * 60)
```

This made tokens immediately expired. It was fixed to:

```ts
.setExpirationTime("15m")
```

Frontend QA behavior:

- `api-client.ts` now gets FastAPI auth token from `/api/auth/backend-token`.
- `api-qa.ts` sends `tabId`, receives streamed `conversationId`, and supports load/rename/delete.
- `legal-qa/page.tsx` no longer renders history in the main content.
- `legal-qa/page.tsx` loads a conversation when URL has `?conversationId=...`.
- `sidebar.tsx` renders Legal QA history under the active `Hỏi đáp pháp lý` nav item.
- Sidebar history can be toggled with up/down arrow.
- Sidebar history supports load, rename, and delete.
- Sidebar history listens for `legal-qa:history-changed` events to refresh after sending a message.

## Environment Setup Notes

Required in `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
AUTH_SECRET=...
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK_API=false
AUTH_RESEND_KEY=...
AUTH_FROM_EMAIL=...
```

`AUTH_RESEND_KEY` comes from Resend, not Supabase.

Supabase keys:

- `NEXT_PUBLIC_SUPABASE_URL`: Supabase project URL.
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`: publishable key.
- `SUPABASE_SERVICE_ROLE_KEY`: secret/service role key. In the new Supabase UI this may start with `sb_secret_...`. Legacy projects may show a JWT service role key.

Security note: real keys were pasted in chat during setup. Rotate Supabase, Resend, Google OAuth, and GitHub OAuth secrets before any shared or production use.

## Commands Used For Verification

Python compile passed:

```bash
python3 -m compileall infra/api src/auth.py src/config.py
```

TypeScript check passed:

```bash
cd frontend
npx tsc --noEmit
```

`npm run build` failed in this environment because Next.js could not fetch Google Fonts (`Kalam`, `Patrick Hand`) from `fonts.googleapis.com`. This was a network/font fetch issue, not a TypeScript error from the chat-session work.

## Known Runtime Issues And Fixes

### 401 Unauthorized from FastAPI QA routes

Cause found:

- `/api/auth/backend-token` returned a token, but token expiration was incorrectly set with `15 * 60`.
- FastAPI treated it as expired.

Fix already applied:

- changed to `.setExpirationTime("15m")`

If 401 still appears:

1. Confirm user is logged in.
2. Open `http://localhost:3000/api/auth/backend-token` and confirm it returns `accessToken`.
3. Restart frontend after env/code changes.
4. Restart backend from repo root:

```bash
cd /home/cuong/Desktop/python/VinUni/nhom104-risk-scanner
uvicorn infra.api.app:app --port 8000 --log-level info
```

### Registration email failure

Cause:

- `AUTH_RESEND_KEY` missing or in wrong file.
- App reads `frontend/.env.local`, not `frontend/.env.local.old`.

Fix:

- Put Resend API key in `frontend/.env.local`.
- Restart frontend.

## Current UI Requirement

The latest requested UI state:

- History must be under the active left-sidebar `Hỏi đáp pháp lý` button.
- It should appear above `Cài đặt`.
- The `Hỏi đáp pháp lý` sidebar item has up/down arrow to show/hide history.
- History is scrollable after about 5 items.
- Main page content should show the QA header and chat, but not the history list.

This was implemented in `frontend/src/components/layout/sidebar.tsx` and `frontend/src/app/(app)/legal-qa/page.tsx`.

## Suggested Next Steps

1. Restart frontend and backend.
2. Log in.
3. Visit `/legal-qa`.
4. Send one question.
5. Confirm Supabase rows:

```sql
SELECT id, user_id, tab_id, title, message_count, last_message_at, deleted_at
FROM chat_conversations
ORDER BY created_at DESC;
```

```sql
SELECT conversation_id, role, sequence, token_count, content
FROM chat_messages
ORDER BY created_at DESC;
```

6. Verify sidebar history appears under `Hỏi đáp pháp lý`.
7. Verify refresh restores same tab conversation.
8. Verify delete sets `deleted_at` and hides the item.
