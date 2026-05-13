## ADDED Requirements

### Requirement: OAuth Login with Google
The system SHALL allow users to authenticate using their Google account via OAuth 2.0.

#### Scenario: Successful Google login
- **WHEN** user clicks "Sign in with Google" button
- **THEN** system redirects to Google OAuth consent screen
- **WHEN** user grants permission
- **THEN** system creates or updates user account and redirects to dashboard

#### Scenario: First-time Google login creates account
- **WHEN** user logs in with Google email not in database
- **THEN** system creates new user record with email, name, and image from Google profile
- **THEN** system assigns default "free" role

#### Scenario: Google login links to existing account
- **WHEN** user logs in with Google email that matches existing account
- **THEN** system links Google provider to existing account
- **THEN** user is logged into existing account

### Requirement: OAuth Login with GitHub
The system SHALL allow users to authenticate using their GitHub account via OAuth 2.0.

#### Scenario: Successful GitHub login
- **WHEN** user clicks "Sign in with GitHub" button
- **THEN** system redirects to GitHub OAuth authorization page
- **WHEN** user authorizes the application
- **THEN** system creates or updates user account and redirects to dashboard

#### Scenario: First-time GitHub login creates account
- **WHEN** user logs in with GitHub email not in database
- **THEN** system creates new user record with email, name, and avatar from GitHub profile
- **THEN** system assigns default "free" role

### Requirement: Email/Password Authentication
The system SHALL allow users to register and login using email and password.

#### Scenario: User registration with email
- **WHEN** user submits valid email and password (min 8 characters)
- **THEN** system creates user record with hashed password
- **THEN** system sends email verification link
- **THEN** user is redirected to verify email page

#### Scenario: User login with email
- **WHEN** user submits valid email and correct password
- **THEN** system authenticates user and creates session
- **THEN** user is redirected to dashboard

#### Scenario: Login with wrong password
- **WHEN** user submits valid email but incorrect password
- **THEN** system returns generic error "Invalid email or password"
- **THEN** system does NOT reveal whether email exists in database

#### Scenario: Password minimum length
- **WHEN** user submits password shorter than 8 characters
- **THEN** system rejects with error "Password must be at least 8 characters"

### Requirement: Email Verification
The system SHALL require email verification before granting full access to the application.

#### Scenario: Verification email sent on registration
- **WHEN** user registers with email/password
- **THEN** system sends verification email via Resend
- **THEN** verification token expires after 24 hours

#### Scenario: User clicks verification link
- **WHEN** user clicks verification link in email
- **THEN** system marks email as verified
- **THEN** user is redirected to dashboard with success message

#### Scenario: Expired verification token
- **WHEN** user clicks verification link after 24 hours
- **THEN** system shows error "Verification link expired"
- **THEN** system offers option to resend verification email

#### Scenario: Unverified user access restriction
- **WHEN** unverified user attempts to access protected routes
- **THEN** system redirects to email verification prompt page
- **THEN** user can request new verification email

### Requirement: Password Reset
The system SHALL allow users to reset their password via email.

#### Scenario: Password reset request
- **WHEN** user submits email on forgot password page
- **THEN** system sends password reset email with time-limited token
- **THEN** system does NOT reveal whether email exists in database

#### Scenario: Password reset with valid token
- **WHEN** user clicks reset link and submits new password
- **THEN** system updates password and invalidates all existing sessions
- **THEN** user is redirected to login page

#### Scenario: Expired reset token
- **WHEN** user uses reset link after token expiry (1 hour)
- **THEN** system shows error "Reset link expired"
- **THEN** system offers option to request new reset link

### Requirement: Session Management
The system SHALL manage user sessions with JWT tokens stored in httpOnly cookies.

#### Scenario: Session creation on login
- **WHEN** user successfully authenticates
- **THEN** system creates JWT with 15-minute expiry
- **THEN** system stores JWT in httpOnly cookie
- **THEN** system creates DB session record for revocation

#### Scenario: Session refresh
- **WHEN** JWT expires and user has valid refresh token
- **THEN** system issues new JWT and rotated refresh token
- **THEN** system updates DB session record

#### Scenario: Session revocation on logout
- **WHEN** user clicks logout
- **THEN** system deletes DB session record
- **THEN** system clears auth cookies
- **THEN** user is redirected to home page

### Requirement: Protected Routes
The system SHALL restrict access to authenticated users for all /app/* routes.

#### Scenario: Unauthenticated access to protected route
- **WHEN** unauthenticated user navigates to /dashboard
- **THEN** system redirects to /login page
- **THEN** system preserves original URL for post-login redirect

#### Scenario: Authenticated access to protected route
- **WHEN** authenticated user navigates to /dashboard
- **THEN** system grants access and renders page

### Requirement: Auth API Client Integration
The system SHALL include authentication headers in all API requests to the backend.

#### Scenario: Authenticated API request
- **WHEN** frontend makes API request to FastAPI backend
- **THEN** request includes JWT in Authorization header as Bearer token

#### Scenario: API request without auth
- **WHEN** unauthenticated frontend makes API request
- **THEN** request is not sent, user is redirected to login
