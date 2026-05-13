## ADDED Requirements

### Requirement: Track linked providers per user
The system SHALL maintain a `linked_providers` JSONB array on each user record to track which authentication providers have been used with that email.

#### Scenario: New user created via Google
- **WHEN** user first logs in with Google
- **THEN** system sets linked_providers = ["google"]

#### Scenario: New user created via Credentials
- **WHEN** user first registers with email/password
- **THEN** system sets linked_providers = ["credentials"]

#### Scenario: Existing Credentials user logs in with Google
- **WHEN** user with linked_providers = ["credentials"] logs in with Google
- **THEN** system updates linked_providers = ["credentials", "google"]

#### Scenario: Existing Google user logs in with GitHub
- **WHEN** user with linked_providers = ["google"] logs in with GitHub
- **THEN** system updates linked_providers = ["google", "github"]

#### Scenario: User logs in with already-linked provider
- **WHEN** user logs in with a provider already in their linked_providers
- **THEN** system does NOT duplicate the provider in the array

### Requirement: linked_providers is queryable for account status checks
The system SHALL be able to query linked_providers to determine which providers are associated with a user account, for display in settings and for account recovery flows.

#### Scenario: Check if user has Credentials provider
- **WHEN** system checks if user has "credentials" in linked_providers
- **THEN** system returns true if "credentials" is in the array, false otherwise

#### Scenario: Check if user has any OAuth provider
- **WHEN** system checks if user has any OAuth provider in linked_providers
- **THEN** system returns true if "google" or "github" is in the array
