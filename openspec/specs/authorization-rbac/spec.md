# authorization-rbac Specification

## Purpose
TBD - created by archiving change add-auth-rbac. Update Purpose after archive.
## Requirements
### Requirement: Role Assignment
The system SHALL assign each user a role from the set: free, premium, admin.

#### Scenario: Default role on registration
- **WHEN** new user registers via any method
- **THEN** system assigns "free" role by default

#### Scenario: Admin role assignment
- **WHEN** admin manually assigns premium or admin role to user
- **THEN** system updates user role in database
- **THEN** new role takes effect on next session refresh

### Requirement: Free Tier Limits
The system SHALL enforce usage limits for users with "free" role.

#### Scenario: Contract upload limit
- **WHEN** free user attempts to upload their 6th contract in a month
- **THEN** system rejects the upload
- **THEN** system displays message prompting upgrade to premium

#### Scenario: Q&A daily limit
- **WHEN** free user attempts to send their 11th question in a day
- **THEN** system rejects the message
- **THEN** system displays message showing limit reset time

#### Scenario: Contract upload within limit
- **WHEN** free user uploads contract within monthly limit (5/month)
- **THEN** system accepts the upload and decrements remaining quota

#### Scenario: Q&A within daily limit
- **WHEN** free user sends question within daily limit (10/day)
- **THEN** system processes the question normally

### Requirement: Premium Tier Access
The system SHALL grant unlimited access to users with "premium" role.

#### Scenario: Unlimited contract uploads
- **WHEN** premium user uploads contract
- **THEN** system accepts without limit check

#### Scenario: Unlimited Q&A
- **WHEN** premium user sends question
- **THEN** system processes without daily limit check

### Requirement: Admin Access
The system SHALL grant full system access to users with "admin" role.

#### Scenario: Admin access to all features
- **WHEN** admin user accesses any feature
- **THEN** system grants access without restriction

#### Scenario: Admin user management
- **WHEN** admin accesses user management interface
- **THEN** system displays list of all users with role management controls

### Requirement: Role-Based API Protection
The system SHALL validate user role on protected API endpoints.

#### Scenario: FastAPI validates JWT role
- **WHEN** API request received at protected endpoint
- **THEN** FastAPI decodes JWT and extracts role claim
- **THEN** endpoint checks role meets minimum requirement

#### Scenario: Insufficient role for endpoint
- **WHEN** user with "free" role accesses premium-only endpoint
- **THEN** system returns 403 Forbidden
- **THEN** response includes message about required tier

### Requirement: Feature Gates
The system SHALL gate features based on user role in the frontend.

#### Scenario: Premium feature visibility
- **WHEN** free user views page with premium features
- **THEN** system shows feature with upgrade prompt overlay
- **THEN** system does NOT hide the feature entirely (discovery)

#### Scenario: Premium feature access
- **WHEN** premium user accesses premium feature
- **THEN** system grants full access without prompts

### Requirement: Usage Counters
The system SHALL track usage counters for free tier limits.

#### Scenario: Contract count tracking
- **WHEN** user uploads contract
- **THEN** system increments monthly contract counter
- **THEN** counter resets on first day of next month

#### Scenario: Q&A count tracking
- **WHEN** user sends question
- **THEN** system increments daily Q&A counter
- **THEN** counter resets at midnight (UTC+7)

#### Scenario: Usage display in UI
- **WHEN** user views dashboard or settings
- **THEN** system displays current usage vs limits (e.g., "3/5 contracts this month")

