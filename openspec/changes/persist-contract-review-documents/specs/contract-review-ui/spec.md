## MODIFIED Requirements

### Requirement: Contract review SHALL support file upload with drag-and-drop
The contract review page SHALL provide a drag-and-drop zone for PDF, DOCX, TXT, and MD files, with a file picker fallback. Uploaded files SHALL be validated for type and size (max 10MB). A successful upload SHALL create a persisted contract document, file version, and review run before showing progress.

#### Scenario: User drags a PDF file onto upload zone
- **WHEN** user drags a .pdf file onto upload zone
- **THEN** the file is accepted, a persisted review run is created, and the user is redirected to the run progress page

#### Scenario: User uploads an invalid file type
- **WHEN** user attempts to upload a .png file
- **THEN** an error message displays: "Chỉ hỗ trợ file PDF, DOCX, TXT và MD"

### Requirement: Contract review SHALL display async job progress
After file upload, the system SHALL create a persisted review run and display a progress page with animated steps (Parsing → Extracting → Retrieving → Analyzing → Verifying → Completed) and a status indicator.

#### Scenario: Progress page shows current step
- **WHEN** user is on the run progress page
- **THEN** the current persisted run status is highlighted with an animated indicator and status text

#### Scenario: User can navigate away and return to job
- **WHEN** user navigates to another page during processing
- **THEN** they can return via the dashboard or run history to see the current persisted status

### Requirement: Contract review SHALL support job history
The contract review page SHALL display a list of previously submitted persisted review runs with status, original filename, date, and quick access to restored results.

#### Scenario: Job history displays past analyses
- **WHEN** user visits the contract review page
- **THEN** a list of recent persisted review runs with status badges (Completed, Processing, Failed) is displayed

#### Scenario: Open completed result from history
- **WHEN** user selects a completed review run from history
- **THEN** the page restores the full review result from the run snapshot

## ADDED Requirements

### Requirement: Contract review SHALL restore results from persisted snapshots
The Contract Review UI SHALL be able to render a completed review result using only the persisted snapshot returned by the backend.

#### Scenario: Refresh completed result page
- **WHEN** user refreshes a completed review result page
- **THEN** the UI reloads the run snapshot and renders the same clauses, matches, compliance report, and citations

#### Scenario: Snapshot unavailable
- **WHEN** user opens a completed run whose snapshot cannot be loaded
- **THEN** the UI shows a recoverable error state instead of starting a new review automatically
