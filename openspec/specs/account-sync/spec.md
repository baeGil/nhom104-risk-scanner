# account-sync Specification

## Purpose
TBD - created by archiving change account-sync. Update Purpose after archive.
## Requirements
### Requirement: Email is the unique identity across all providers
The system SHALL treat email as the unique identifier for users across all authentication providers (Credentials, Google, GitHub). When a user attempts to authenticate with an email that already exists in the database, the system SHALL return the existing user row instead of creating a new one.

#### Scenario: Google login with existing email from Credentials registration
- **WHEN** user logs in with Google using an email that already has a Credentials account
- **THEN** system returns the existing user row
- **THEN** system adds "google" to the user's linked_providers array
- **THEN** system does NOT create a new user row
- **THEN** system does NOT update the user's name or image

#### Scenario: GitHub login with existing email from Google login
- **WHEN** user logs in with GitHub using an email that already has a Google-linked account
- **THEN** system returns the existing user row
- **THEN** system adds "github" to the user's linked_providers array
- **THEN** system does NOT create a new user row

#### Scenario: Credentials registration with existing email from OAuth
- **WHEN** user attempts to register with email/password using an email that already has an OAuth-linked account
- **THEN** system returns an error indicating the email is already linked to a provider
- **THEN** system offers the option to set a password for the existing account
- **THEN** if user chooses to set password, system adds "credentials" to linked_providers and sets password_hash

### Requirement: Name and image are set on first account creation only
The system SHALL set the user's name and image from the provider used during the first account creation. Subsequent logins from different providers SHALL NOT override the name or image.

#### Scenario: First account created via Google
- **WHEN** user first logs in with Google
- **THEN** system sets name and image from Google profile
- **THEN** subsequent Credentials or GitHub logins do NOT change name or image

#### Scenario: First account created via Credentials registration
- **WHEN** user first registers with email/password
- **THEN** system sets name from the registration form (or email prefix if not provided)
- **THEN** subsequent Google or GitHub logins do NOT change name or image

### Requirement: OAuth login does not require email verification
Users who authenticate via OAuth providers (Google, GitHub) SHALL have their email marked as verified automatically, as the OAuth provider has already verified the email.

#### Scenario: Google login for new user
- **WHEN** user logs in with Google for the first time
- **THEN** system creates user with email_verified set to current timestamp
- **THEN** system does NOT send OTP verification email

#### Scenario: GitHub login for new user
- **WHEN** user logs in with GitHub for the first time
- **THEN** system creates user with email_verified set to current timestamp
- **THEN** system does NOT send OTP verification email

### Requirement: OAuth-only users can set password via forgot-password flow
Users who have only authenticated via OAuth (no password_hash) SHALL be able to set a password through the forgot-password flow without re-verifying their email.

#### Scenario: OAuth-only user sets password
- **WHEN** user with no password_hash requests password reset
- **THEN** system sends reset link to their email
- **WHEN** user clicks link and sets new password
- **THEN** system sets password_hash for the user
- **THEN** user can now log in with both OAuth and Credentials

