# session-monitor Specification

## Purpose
TBD - created by archiving change auth-sync-tabs. Update Purpose after archive.
## Requirements
### Requirement: Periodic session check every 5 minutes
The system SHALL check session validity every 5 minutes by fetching the session endpoint. If the session is invalid or expired, the system SHALL broadcast a 'session-expired' event to all tabs.

#### Scenario: Session check passes
- **WHEN** periodic check runs and session is valid
- **THEN** system does nothing

#### Scenario: Session check fails
- **WHEN** periodic check runs and session is invalid/expired
- **THEN** system broadcasts 'session-expired' event
- **THEN** all tabs show AuthExpiredModal

### Requirement: 401 interceptor detects revoked tokens
The system SHALL intercept 401 responses from API calls and check if the session has expired. If so, the system SHALL broadcast a 'session-expired' event.

#### Scenario: API call returns 401
- **WHEN** any API call returns 401 status
- **THEN** system fetches session to confirm expiration
- **THEN** if session is expired, broadcasts 'session-expired' event

