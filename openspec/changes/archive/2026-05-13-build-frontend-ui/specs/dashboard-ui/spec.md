## ADDED Requirements

### Requirement: Dashboard SHALL display overview statistics
The dashboard SHALL show key metrics: total contracts reviewed, total questions asked, system health status, and knowledge graph coverage (documents, nodes, relationships).

#### Scenario: Stats cards display on dashboard load
- **WHEN** user visits /dashboard
- **THEN** 4 stat cards display with current values in hand-drawn card style

### Requirement: Dashboard SHALL display recent contracts list
The dashboard SHALL show a list of the 5 most recent contract review jobs with filename, status, date, and a link to view results.

#### Scenario: Recent contracts display with status badges
- **WHEN** user visits /dashboard
- **THEN** a list of recent contracts shows filename, status (Completed/Processing/Failed), and date

### Requirement: Dashboard SHALL display recent questions list
The dashboard SHALL show the 5 most recent legal QA conversations with the question preview, detected domain, and date.

#### Scenario: Recent questions display with domain tags
- **WHEN** user visits /dashboard
- **THEN** a list of recent questions shows the question text, domain tag, and timestamp

### Requirement: Dashboard SHALL provide quick action navigation
The dashboard SHALL include prominent navigation cards to Contract Review, Legal QA, Settings, and Upgrade pages.

#### Scenario: Quick action cards navigate to respective pages
- **WHEN** user clicks a quick action card (e.g., "Rà soát hợp đồng")
- **THEN** the user is navigated to the corresponding page

### Requirement: Dashboard SHALL be responsive
The dashboard layout SHALL adapt from single column on mobile to multi-column on desktop.

#### Scenario: Dashboard collapses on mobile
- **WHEN** viewport width is below 768px
- **THEN** all dashboard sections stack vertically in a single column
