## MODIFIED Requirements

### Requirement: Contract review SHALL display clause list as sticky-note cards
The results page SHALL display extracted contract clauses from the real backend job as individual sticky-note style cards with clause type, text preview, risk level indicator, and access to matched legal provisions for the clause.

#### Scenario: Clauses display as cards with risk colors
- **WHEN** the contract analysis is complete
- **THEN** each clause is displayed as a card with a colored risk indicator (green/yellow/red)

#### Scenario: Clause shows legal matches
- **WHEN** a clause has matched legal provisions
- **THEN** the clause card or detail panel displays top legal matches with document title, article, clause, point, and score explanation when available

### Requirement: Contract review SHALL display compliance report with annotations
The results page SHALL include a compliance report section showing real violations, risks, suggestions, and matched legal context from the backend. Violations SHALL use red correction marker styling and suggestions SHALL be tied to the relevant clause when possible.

#### Scenario: Violations are highlighted in red
- **WHEN** a compliance violation is detected
- **THEN** it is displayed with red accent color and a warning icon

#### Scenario: Suggestions link to clauses
- **WHEN** a suggestion is generated for a specific clause
- **THEN** the UI shows the suggestion near or linked to that clause

### Requirement: Contract review SHALL display citation verification badges
Each cited legal provision SHALL have a verification badge showing VERIFIED (green check) or UNVERIFIED (gray question mark). The citation display SHALL include document title and the fullest available Điều/Khoản/Điểm path.

#### Scenario: Verified citation shows green badge
- **WHEN** a citation is verified against the knowledge graph
- **THEN** a green check badge with "VERIFIED" text is displayed

#### Scenario: Unverified citation shows gray badge
- **WHEN** a citation cannot be verified
- **THEN** a gray question mark badge with "UNVERIFIED" text is displayed

#### Scenario: Citation shows hierarchy path
- **WHEN** a citation references a point-level legal segment
- **THEN** the UI displays document title, article, clause, and point when available

### Requirement: Contract review SHALL support job history
The contract review page SHALL display a list of previously submitted persisted jobs with status, date, filename, quick access to results, and failure messages when available.

#### Scenario: Job history displays past analyses
- **WHEN** user visits the contract review page
- **THEN** a list of recent jobs with status badges (Completed, Processing, Failed) is displayed

#### Scenario: Reopen completed job
- **WHEN** user selects a completed job from history
- **THEN** the UI loads persisted clauses, matches, compliance, and citation verification results
