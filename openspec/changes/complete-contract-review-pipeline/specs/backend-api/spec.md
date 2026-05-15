## MODIFIED Requirements

### Requirement: Contract upload endpoint
The system SHALL provide a POST /api/contracts/upload endpoint that accepts multipart/form-data with a file field. The endpoint SHALL validate file type (PDF, DOCX, TXT, MD) and size (max 10MB), create a persisted contract review job, initiate real async processing through parser, clause extraction, query rewrite, hybrid retrieval, compliance analysis, and citation verification, and return { jobId: string }. The endpoint SHALL NOT return fabricated mock analysis for production jobs.

#### Scenario: Upload valid contract
- **WHEN** client uploads a PDF file
- **THEN** system returns a jobId for async processing

#### Scenario: Reject invalid file type
- **WHEN** client uploads a PNG file
- **THEN** system returns 400 with error message

#### Scenario: Start real processing
- **WHEN** client uploads a valid contract
- **THEN** the created job is processed by the real contract review pipeline rather than the mock fixture path

### Requirement: Contract job status endpoint
The system SHALL provide GET /api/contracts/{jobId}/status returning { jobId, status, progress, filename, createdAt, clauses?, matches?, compliance?, citations?, error? }. Status values SHALL be: "uploading", "parsing", "extracting", "retrieving", "analyzing", "verifying", "completed", "failed". Progress SHALL be 0-100 and SHALL reflect the current pipeline stage.

#### Scenario: Check job progress
- **WHEN** client GETs /api/contracts/job_001/status
- **THEN** system returns current status and progress

#### Scenario: Return completed real results
- **WHEN** client requests a completed job
- **THEN** system returns persisted extracted clauses, legal matches, compliance output, and citation verification statuses

#### Scenario: Return failed job error
- **WHEN** a processing stage fails
- **THEN** system returns status="failed" with an error message and no fabricated compliance result

### Requirement: Contract job history endpoint
The system SHALL provide GET /api/contracts/history returning an array of persisted JobStatusResponse objects for the current user, sorted by createdAt descending. The response SHALL include enough summary data for the frontend to reopen completed, failed, or in-progress jobs.

#### Scenario: Get job history
- **WHEN** client GETs /api/contracts/history
- **THEN** system returns all jobs sorted by date

#### Scenario: History survives restart
- **WHEN** the backend restarts after jobs have completed
- **THEN** job history remains available from durable storage
