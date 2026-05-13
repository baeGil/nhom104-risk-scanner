## ADDED Requirements

### Requirement: Settings page SHALL display user profile section
The settings page SHALL show a profile section with name, email, and avatar placeholder, all editable with hand-drawn form inputs.

#### Scenario: Profile displays current user info
- **WHEN** user visits /settings
- **THEN** their name, email, and a placeholder avatar are displayed in editable fields

### Requirement: Settings page SHALL display API key management
The settings page SHALL include a section for managing API keys with the ability to generate, copy, and revoke keys.

#### Scenario: User can view and copy API key
- **WHEN** user has an API key
- **THEN** the key is displayed (partially masked) with a copy button

#### Scenario: User can generate a new API key
- **WHEN** user clicks "Tạo key mới"
- **THEN** a new API key is generated and displayed

### Requirement: Settings page SHALL display preferences section
The settings page SHALL include preference toggles for notification settings, language preference, and theme options.

#### Scenario: Preferences display as toggles
- **WHEN** user visits /settings
- **THEN** preference options display as toggle switches with hand-drawn styling

### Requirement: Upgrade page SHALL display pricing tiers
The upgrade page SHALL show 3 pricing tiers (Free, Pro, Team) with feature comparison, styled as post-it notes with wobbly borders.

#### Scenario: Pricing tiers display with feature lists
- **WHEN** user visits /upgrade
- **THEN** 3 pricing cards display with tier name, price, feature list, and CTA button

### Requirement: Upgrade page SHALL highlight recommended tier
The Pro tier SHALL be visually highlighted (scaled up, different background color, "Phổ biến" badge) to draw attention.

#### Scenario: Pro tier is visually distinct
- **WHEN** pricing tiers are displayed
- **THEN** the Pro card is slightly larger with a yellow background and a "Phổ biến" sticky-note tag
