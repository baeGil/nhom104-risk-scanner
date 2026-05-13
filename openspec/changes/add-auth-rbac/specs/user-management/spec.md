## ADDED Requirements

### Requirement: User Profile Display
The system SHALL display authenticated user's profile information in the application.

#### Scenario: Profile display in settings
- **WHEN** authenticated user visits /settings page
- **THEN** system displays user's name, email, and avatar from their account
- **THEN** system shows current subscription tier and role

#### Scenario: OAuth user profile
- **WHEN** user authenticated via Google or GitHub
- **THEN** system displays name and avatar from OAuth provider

### Requirement: User Profile Update
The system SHALL allow users to update their profile information.

#### Scenario: Update display name
- **WHEN** user submits new display name
- **THEN** system updates name in database
- **THEN** system displays success confirmation

#### Scenario: Email update restriction
- **WHEN** user attempts to change email address
- **THEN** system requires re-verification of new email
- **THEN** original email remains active until new email is verified

### Requirement: Account Deletion
The system SHALL allow users to delete their account.

#### Scenario: Account deletion request
- **WHEN** user requests account deletion from settings
- **THEN** system shows confirmation dialog with data loss warning
- **THEN** upon confirmation, system soft-deletes user record
- **THEN** system revokes all active sessions

#### Scenario: Post-deletion access
- **WHEN** deleted user attempts to login
- **THEN** system treats as new registration

### Requirement: Session Management UI
The system SHALL display active sessions and allow users to revoke them.

#### Scenario: View active sessions
- **WHEN** user visits settings > security section
- **THEN** system lists active sessions with device info and last activity time

#### Scenario: Revoke all sessions
- **WHEN** user clicks "Sign out all devices"
- **THEN** system revokes all DB sessions for the user
- **THEN** current session is also terminated

### Requirement: Current Plan Display
The system SHALL display the user's current subscription plan and usage.

#### Scenario: Free user plan display
- **WHEN** free user views settings or upgrade page
- **THEN** system shows current plan as "Miễn phí" with usage counters
- **THEN** system shows remaining quota (e.g., "2/5 contracts remaining")

#### Scenario: Premium user plan display
- **WHEN** premium user views settings
- **THEN** system shows current plan as "Chuyên nghiệp" with "Unlimited" indicators

### Requirement: Upgrade Prompt
The system SHALL prompt free users to upgrade when they hit limits.

#### Scenario: Upgrade prompt on limit reached
- **WHEN** free user hits contract or Q&A limit
- **THEN** system displays modal with upgrade prompt
- **THEN** modal shows comparison of free vs premium features

#### Scenario: Upgrade page access
- **WHEN** user navigates to /upgrade
- **THEN** system displays pricing tiers (Free, Professional, Enterprise)
- **THEN** system highlights user's current plan
