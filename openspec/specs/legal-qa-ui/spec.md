# legal-qa-ui Specification

## Purpose
TBD - created by archiving change build-frontend-ui. Update Purpose after archive.
## Requirements
### Requirement: Legal QA SHALL provide chat interface with speech bubbles
The legal QA page SHALL display a chat interface where user messages appear as right-aligned speech bubbles and AI responses appear as left-aligned speech bubbles, both with hand-drawn styling.

#### Scenario: User message displays as right-aligned bubble
- **WHEN** user sends a question
- **THEN** the message appears as a right-aligned speech bubble with blue accent border

#### Scenario: AI response displays as left-aligned bubble
- **WHEN** the AI responds
- **THEN** the response appears as a left-aligned speech bubble with white background and wobbly border

### Requirement: Legal QA SHALL stream AI responses via SSE
The system SHALL connect to the backend via Server-Sent Events (SSE) and display AI responses token-by-token with a typing cursor animation.

#### Scenario: Response streams token by token
- **WHEN** the AI begins responding
- **THEN** text appears incrementally with a blinking cursor at the end

#### Scenario: Streaming completes gracefully
- **WHEN** the SSE stream ends
- **THEN** the cursor disappears and the full response is displayed

### Requirement: Legal QA SHALL display detected intent tags
Each AI response SHALL be preceded by intent tags showing the detected domain (QA, CONTRACT_REVIEW, EXPLAIN, etc.) and intent types (LOOKUP, VALIDITY, COMPARISON, etc.) with confidence scores.

#### Scenario: Intent tags display above response
- **WHEN** an AI response is received
- **THEN** colored tags showing domain and intent types appear above the response bubble

### Requirement: Legal QA SHALL display retrieved provision cards
The AI response SHALL include clickable provision cards showing the retrieved legal articles with document name, article number, and a snippet of the effective text.

#### Scenario: Provision cards display with source info
- **WHEN** provisions are retrieved for a response
- **THEN** cards appear below the response with document name, article number, and text snippet

### Requirement: Legal QA SHALL support multi-turn conversations
The chat interface SHALL maintain conversation history within a session, allowing follow-up questions that reference previous context.

#### Scenario: Follow-up question references previous context
- **WHEN** user asks "Điều khoản đó còn hiệu lực không?" after discussing a specific article
- **THEN** the system resolves "điều khoản đó" to the previously discussed article

### Requirement: Legal QA SHALL display citation verification badges
Citations in AI responses SHALL have verification badges (VERIFIED/UNVERIFIED) matching the contract review citation style.

#### Scenario: Citation in response shows verification status
- **WHEN** an AI response cites a legal provision
- **THEN** the citation includes a VERIFIED or UNVERIFIED badge

### Requirement: Legal QA SHALL support conversation management
The chat interface SHALL allow users to start a new conversation, view conversation history, and delete conversations.

#### Scenario: User starts a new conversation
- **WHEN** user clicks "Cuộc trò chuyện mới"
- **THEN** the chat clears and a fresh conversation begins

