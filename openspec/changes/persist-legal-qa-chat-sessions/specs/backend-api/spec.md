## MODIFIED Requirements

### Requirement: QA chat endpoint with SSE streaming
The system SHALL provide a POST /api/qa/chat endpoint that accepts { message: string, conversationId?: string, tabId?: string } and returns an SSE stream of ChatChunk objects. Each chunk SHALL have the format: data: {"token": "..."} for text tokens, data: {"intents": [...], "provisions": [...]} for metadata, data: {"conversationId": "..."} when a new conversation is created, and data: [DONE] for stream termination. The endpoint SHALL process the message through the full QA pipeline: intent analysis -> retrieval -> answer generation -> citation verification. The endpoint SHALL persist the user message and assistant message in Supabase under the authenticated user, including token_count, intents, provisions, and citations.

#### Scenario: Stream QA response
- **WHEN** an authenticated client POSTs a question to /api/qa/chat
- **THEN** system streams the answer token-by-token via SSE
- **THEN** system persists the user and assistant messages in chat_messages

#### Scenario: Include intents and provisions in stream
- **WHEN** intent analysis and retrieval complete
- **THEN** intents and provisions are sent as a mid-stream SSE chunk
- **THEN** the assistant message stores those intents and provisions as JSONB metadata

#### Scenario: Include citations in persisted assistant message
- **WHEN** citation verification completes for an assistant answer
- **THEN** the assistant message stores citation metadata in chat_messages.citations

#### Scenario: Create conversation on first message
- **WHEN** authenticated client POSTs a question without conversationId and with a tabId
- **THEN** system creates a chat_conversations row owned by the authenticated user
- **THEN** system includes the new conversationId in the SSE stream

#### Scenario: Terminate stream gracefully
- **WHEN** answer generation completes
- **THEN** stream ends with data: [DONE]

### Requirement: Conversation management endpoints
The system SHALL provide POST /api/qa/conversations to create a new conversation (returns { id: string }), GET /api/qa/conversations to list active conversations sorted by lastMessageAt descending (returns array of { id, title, lastMessage, createdAt, lastMessageAt }), GET /api/qa/conversations/{id} to load messages for an active conversation owned by the authenticated user, PATCH /api/qa/conversations/{id} to rename a conversation, and DELETE /api/qa/conversations/{id} to soft-delete a conversation by setting deleted_at. All endpoints SHALL scope reads and writes to the authenticated user.

#### Scenario: Create conversation
- **WHEN** authenticated client POSTs to /api/qa/conversations with a tabId
- **THEN** system creates a new chat_conversations row for the authenticated user and returns its ID

#### Scenario: List conversations
- **WHEN** authenticated client GETs /api/qa/conversations
- **THEN** system returns non-deleted conversations owned by the authenticated user sorted by lastMessageAt descending

#### Scenario: Load conversation messages
- **WHEN** authenticated client GETs /api/qa/conversations/{id}
- **THEN** system returns ordered chat_messages for that conversation only if it belongs to the authenticated user and is not deleted

#### Scenario: Rename conversation
- **WHEN** authenticated client PATCHes /api/qa/conversations/{id} with a title
- **THEN** system updates the title and marks title_source as manual only if the conversation belongs to the authenticated user

#### Scenario: Delete conversation
- **WHEN** authenticated client DELETEs /api/qa/conversations/{id}
- **THEN** system sets deleted_at on the conversation owned by that user
- **THEN** system excludes that conversation from future list and load results
