## ADDED Requirements

### Requirement: User receives OTP via email after registration
After successful email/password registration, the system SHALL generate a 6-digit OTP code, hash it with SHA-256 using AUTH_SECRET as salt, store it in `email_otp_codes` with 10-minute expiry, and send a branded email containing both the OTP code and a verification link.

#### Scenario: New user registers with valid email
- **WHEN** user submits registration form with valid email and password
- **THEN** system creates user with `email_verified = null`
- **THEN** system generates 6-digit OTP, hashes it, stores with 10-minute expiry
- **THEN** system sends branded email with OTP code and verification link
- **THEN** system redirects user to `/verify-otp?email=<email>`

#### Scenario: User re-registers with unverified email
- **WHEN** user registers with an email that exists but is not verified
- **THEN** system invalidates previous OTP (marks `is_used = true`)
- **THEN** system generates new OTP and sends email
- **THEN** system redirects user to `/verify-otp?email=<email>`

### Requirement: User can verify OTP code
The system SHALL provide an endpoint `/api/auth/verify-otp` that accepts a 6-digit code, validates it against the stored hash, and returns a one-time auto-login token on success.

#### Scenario: User enters correct OTP
- **WHEN** user submits correct 6-digit code within 10 minutes
- **THEN** system marks OTP as used, sets `email_verified` to current timestamp
- **THEN** system generates one-time auto-login token (JWT, 2-minute expiry)
- **THEN** system returns 200 with `{ tempToken: "..." }`

#### Scenario: User enters incorrect OTP
- **WHEN** user submits incorrect 6-digit code
- **THEN** system increments `failed_count`
- **THEN** system returns 401 with error message "Mã không đúng"

#### Scenario: User exceeds 5 failed attempts
- **WHEN** user submits 5th incorrect code
- **THEN** system sets `locked_until` to current time + 15 minutes
- **THEN** system returns 429 with error message "Đã khóa 15 phút"

#### Scenario: User attempts verification while locked
- **WHEN** user submits any code while `locked_until > now()`
- **THEN** system returns 429 with remaining lock time

#### Scenario: OTP expired
- **WHEN** user submits code after 10-minute expiry
- **THEN** system returns 400 with error message "Mã đã hết hạn"

### Requirement: User can resend OTP
The system SHALL provide an endpoint `/api/auth/resend-otp` that generates a new OTP with 60-second cooldown, invalidating the previous one.

#### Scenario: User requests resend after cooldown
- **WHEN** user clicks resend after 60 seconds
- **THEN** system marks previous OTP as used
- **THEN** system generates new OTP, sends email, resets `failed_count`
- **THEN** system returns 200 with success message

#### Scenario: User requests resend before cooldown
- **WHEN** user clicks resend within 60 seconds of last send
- **THEN** system returns 429 with remaining cooldown time

### Requirement: Auto-login after OTP verification
The system SHALL provide an endpoint `/api/auth/auto-login` that accepts a one-time temp token, creates a session, and redirects to dashboard.

#### Scenario: User submits valid temp token
- **WHEN** user submits valid, unused temp token within 2-minute expiry
- **THEN** system marks token as used
- **THEN** system creates Auth.js session cookie
- **THEN** system returns 200 with `{ redirect: "/dashboard" }`

#### Scenario: User submits expired or used temp token
- **WHEN** user submits expired or already-used temp token
- **THEN** system returns 400 with error message

### Requirement: Credentials login requires email verification
The Auth.js `signIn` callback SHALL reject credentials login if `email_verified` is null.

#### Scenario: Unverified user attempts login
- **WHEN** user with `email_verified = null` submits login form
- **THEN** system rejects with error "Vui lòng xác thực email trước khi đăng nhập"

#### Scenario: Verified user attempts login
- **WHEN** user with `email_verified != null` submits login form
- **THEN** system allows login normally

### Requirement: OAuth login bypasses email verification
Users who register via Google or GitHub SHALL NOT be required to verify email, as the OAuth provider has already verified their email.

#### Scenario: User logs in via Google
- **WHEN** user signs in with Google
- **THEN** system creates/updates user with `email_verified = current timestamp`
- **THEN** system allows login without OTP verification

#### Scenario: User logs in via GitHub
- **WHEN** user signs in with GitHub
- **THEN** system creates/updates user with `email_verified = current timestamp`
- **THEN** system allows login without OTP verification

### Requirement: Email verification link still works
The existing `/verify-email` endpoint SHALL continue to work, marking email as verified and enabling auto-login.

#### Scenario: User clicks verification link in email
- **WHEN** user clicks link with valid token
- **THEN** system marks `email_verified` to current timestamp
- **THEN** system invalidates corresponding OTP
- **THEN** system redirects to `/login` or auto-logs in
