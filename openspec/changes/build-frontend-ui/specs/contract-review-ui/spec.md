## ADDED Requirements

### Requirement: Contract review SHALL support file upload with drag-and-drop
The contract review page SHALL provide a drag-and-drop zone for PDF and DOCX files, with a file picker fallback. Uploaded files SHALL be validated for type and size (max 10MB).

#### Scenario: User drags a PDF file onto upload zone
- **WHEN** user drags a .pdf file onto the upload zone
- **THEN** the file is accepted, a job is created, and the user is redirected to the job progress page

#### Scenario: User uploads an invalid file type
- **WHEN** user attempts to upload a .png file
- **THEN** an error message displays: "Chỉ hỗ trợ file PDF và DOCX"

### Requirement: Contract review SHALL display async job progress
After file upload, the system SHALL create an async job and display a progress page with animated steps (Parsing → Analyzing → Generating Report) and a progress indicator.

#### Scenario: Progress page shows current step
- **WHEN** user is on the job progress page
- **THEN** the current step is highlighted with an animated indicator and status text

#### Scenario: User can navigate away and return to job
- **WHEN** user navigates to another page during processing
- **THEN** they can return via the dashboard or job history to see the current progress

### Requirement: Contract review SHALL display clause list as sticky-note cards
The results page SHALL display extracted contract clauses as individual sticky-note style cards with clause type, text preview, and risk level indicator.

#### Scenario: Clauses display as cards with risk colors
- **WHEN** the contract analysis is complete
- **THEN** each clause is displayed as a card with a colored risk indicator (green/yellow/red)

### Requirement: Contract review SHALL display compliance report with annotations
The results page SHALL include a compliance report section showing violations, risks, and suggestions with red correction marker styling for violations.

#### Scenario: Violations are highlighted in red
- **WHEN** a compliance violation is detected
- **THEN** it is displayed with red accent color and a warning icon

### Requirement: Contract review SHALL display citation verification badges
Each cited legal provision SHALL have a verification badge showing VERIFIED (green check) or UNVERIFIED (gray question mark).

#### Scenario: Verified citation shows green badge
- **WHEN** a citation is verified against the knowledge graph
- **THEN** a green check badge with "VERIFIED" text is displayed

#### Scenario: Unverified citation shows gray badge
- **WHEN** a citation cannot be verified
- **THEN** a gray question mark badge with "UNVERIFIED" text is displayed

### Requirement: Contract review SHALL support job history
The contract review page SHALL display a list of previously submitted jobs with status, date, and quick access to results.

#### Scenario: Job history displays past analyses
- **WHEN** user visits the contract review page
- **THEN** a list of recent jobs with status badges (Completed, Processing, Failed) is displayed
