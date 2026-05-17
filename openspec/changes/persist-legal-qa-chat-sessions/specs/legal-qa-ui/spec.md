## MODIFIED Requirements

### Requirement: Legal QA SHALL support multi-turn conversations
The chat interface SHALL maintain persistent conversation history for authenticated users, allowing follow-up questions that reference previous context. The active browser tab SHALL restore its current conversation after refresh by using a tab-scoped identifier stored in sessionStorage.

#### Scenario: Follow-up question references previous context
- **WHEN** user asks "Điều khoản đó còn hiệu lực không?" after discussing a specific article
- **THEN** the system resolves "điều khoản đó" to the previously discussed article

#### Scenario: Refresh restores tab conversation
- **WHEN** user refreshes a Legal QA browser tab after sending at least one message
- **THEN** the chat interface reloads the same conversation and message history for that tab

#### Scenario: New tab starts separate conversation
- **WHEN** user opens Legal QA in a separate browser tab and sends a first message
- **THEN** the system creates a separate conversation for that tab

### Requirement: Legal QA SHALL support conversation management
The chat interface SHALL allow authenticated users to start a new conversation, view persistent conversation history sorted by last message time, rename conversations, load prior conversations, and delete conversations through soft delete.

#### Scenario: User starts a new conversation
- **WHEN** user clicks "Cuộc trò chuyện mới"
- **THEN** the chat clears and a fresh tab conversation begins

#### Scenario: User views conversation history
- **WHEN** user opens the Legal QA conversation history
- **THEN** the UI lists non-deleted conversations for the authenticated user sorted by last message time

#### Scenario: User loads previous conversation
- **WHEN** user selects a conversation from history
- **THEN** the UI loads its persisted messages, citations, provisions, and intents

#### Scenario: User renames conversation
- **WHEN** user edits a conversation title
- **THEN** the UI persists the manual title and displays it in conversation history

#### Scenario: User deletes conversation
- **WHEN** user deletes a conversation
- **THEN** the UI removes it from history without hard-deleting its stored messages
