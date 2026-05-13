## ADDED Requirements

### Requirement: Branded verification email template
The system SHALL send a branded HTML email for OTP verification that includes the PhápLý logo, brand colors (#2563eb), clear OTP display, and a verification link button.

#### Scenario: New user receives verification email
- **WHEN** user registers with email/password
- **THEN** email includes PhápLý branding (logo, colors)
- **THEN** email displays 6-digit OTP in large, prominent format
- **THEN** email includes "Xác thực email" button with verification link
- **THEN** email states OTP expiry time (10 minutes)
- **THEN** email includes footer with "If you didn't create this account, ignore this email"

#### Scenario: Email renders correctly across clients
- **WHEN** email is viewed in Gmail, Outlook, Apple Mail
- **THEN** inline styles ensure consistent rendering
- **THEN** OTP code is readable without clicking

### Requirement: Email sent via Resend SDK
The system SHALL use the Resend SDK to send verification emails, with configurable `from` address via `AUTH_FROM_EMAIL` environment variable.

#### Scenario: Email delivery
- **WHEN** system sends verification email
- **THEN** email is sent via Resend API
- **THEN** `from` address uses `AUTH_FROM_EMAIL` or defaults to "onboarding@resend.dev"
