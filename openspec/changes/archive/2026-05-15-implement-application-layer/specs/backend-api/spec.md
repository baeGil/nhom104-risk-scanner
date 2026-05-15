## ADDED Requirements

### Requirement: QA chat endpoint with SSE streaming
The system SHALL provide a POST /api/qa/chat endpoint that accepts { message: string, conversationId: string } and returns an SSE stream of ChatChunk objects. Each chunk SHALL have the format: data: {"token": "..."} for text tokens, data: {"intents": [...], "provisions": [...]} for metadata, and data: [DONE] for stream termination. The endpoint SHALL process the message through the full QA pipeline: intent analysis → retrieval → answer generation → citation verification.

#### Scenario: Stream QA response
- **WHEN** client POSTs a question to /api/qa/chat
- **THEN** system streams the answer token-by-token via SSE

#### Scenario: Include intents and provisions in stream
- **WHEN** intent analysis and retrieval complete
- **THEN** intents and provisions are sent as a mid-stream SSE chunk

#### Scenario: Terminate stream gracefully
- **WHEN** answer generation completes
- **THEN** stream ends with data: [DONE]

### Requirement: Conversation management endpoints
The system SHALL provide POST /api/qa/conversations to create a new conversation (returns { id: string }), GET /api/qa/conversations to list all conversations (returns array of { id, title, lastMessage, createdAt }), and DELETE /api/qa/conversations/{id} to delete a conversation.

#### Scenario: Create conversation
- **WHEN** client POSTs to /api/qa/conversations
- **THEN** system creates a new conversation and returns its ID

#### Scenario: List conversations
- **WHEN** client GETs /api/qa/conversations
- **THEN** system returns all conversations with summaries

### Requirement: Contract upload endpoint
The system SHALL provide a POST /api/contracts/upload endpoint that accepts multipart/form-data with a file field. The endpoint SHALL validate file type (PDF, DOCX, TXT) and size (max 10MB), initiate async processing, and return { jobId: string }.

#### Scenario: Upload valid contract
- **WHEN** client uploads a PDF file
- **THEN** system returns a jobId for async processing

#### Scenario: Reject invalid file type
- **WHEN** client uploads a PNG file
- **THEN** system returns 400 with error message

### Requirement: Contract job status endpoint
The system SHALL provide GET /api/contracts/{jobId}/status returning { jobId, status, progress, filename, createdAt, clauses?, compliance? }. Status values SHALL be: "uploading", "parsing", "analyzing", "completed", "failed". Progress SHALL be 0-100.

#### Scenario: Check job progress
- **WHEN** client GETs /api/contracts/job_001/status
- **THEN** system returns current status and progress

### Requirement: Contract job history endpoint
The system SHALL provide GET /api/contracts/history returning an array of JobStatusResponse objects for all jobs, sorted by createdAt descending.

#### Scenario: Get job history
- **WHEN** client GETs /api/contracts/history
- **THEN** system returns all jobs sorted by date

### Requirement: CORS configuration
The backend SHALL allow cross-origin requests from the Next.js frontend (http://localhost:3000 in development) with appropriate CORS headers for all endpoints.

#### Scenario: Allow frontend origin
- **WHEN** frontend sends request from http://localhost:3000
- **THEN** backend responds with Access-Control-Allow-Origin header
