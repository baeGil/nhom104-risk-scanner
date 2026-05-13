## ADDED Requirements

### Requirement: Login page SHALL provide email/password form with hand-drawn styling
The login page SHALL display a form with email and password inputs styled with wobbly borders, a "Đăng nhập" button, and a link to the register page.

#### Scenario: Login form renders with hand-drawn inputs
- **WHEN** user visits /login
- **THEN** a form with wobbly-styled email and password inputs and a submit button is displayed

#### Scenario: Form validates empty fields
- **WHEN** user clicks "Đăng nhập" with empty fields
- **THEN** validation messages appear below the empty inputs

### Requirement: Register page SHALL provide account creation form
The register page SHALL display a form with name, email, password, and confirm password inputs with hand-drawn styling.

#### Scenario: Register form renders
- **WHEN** user visits /register
- **THEN** a form with name, email, password, and confirm password inputs is displayed

### Requirement: Auth pages SHALL be placeholders without actual authentication gate
The login and register pages SHALL exist and be navigable, but SHALL NOT block access to any application routes. All routes SHALL be accessible without authentication during development.

#### Scenario: User can navigate to app pages without logging in
- **WHEN** user visits /dashboard directly without logging in
- **THEN** the dashboard page loads normally without redirect to /login

#### Scenario: Login form submission does not block navigation
- **WHEN** user submits the login form with any input
- **THEN** the user is not redirected or blocked; the form accepts any input for testing purposes
