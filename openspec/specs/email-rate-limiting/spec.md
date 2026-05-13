# email-rate-limiting Specification

## Purpose
TBD - created by archiving change email-otp-verification. Update Purpose after archive.
## Requirements
### Requirement: Per-IP rate limiting for OTP requests
The system SHALL limit OTP-related requests to 10 per hour per IP address. This includes OTP generation during registration and resend requests.

#### Scenario: IP within rate limit
- **WHEN** IP has made fewer than 10 OTP requests in the current hour
- **THEN** system allows the request

#### Scenario: IP exceeds OTP rate limit
- **WHEN** IP has made 10 OTP requests in the current hour
- **THEN** system returns 429 with error message "Quá nhiều yêu cầu. Vui lòng thử lại sau"

### Requirement: Per-IP rate limiting for registrations
The system SHALL limit new account registrations to 3 per hour per IP address.

#### Scenario: IP within registration limit
- **WHEN** IP has made fewer than 3 registrations in the current hour
- **THEN** system allows registration

#### Scenario: IP exceeds registration rate limit
- **WHEN** IP has made 3 registrations in the current hour
- **THEN** system returns 429 with error message "Quá nhiều tài khoản tạo từ IP này. Vui lòng thử lại sau"

### Requirement: Rate limiting uses abstracted service interface
The rate limiting implementation SHALL use a `RateLimitService` interface that abstracts the storage backend, allowing future migration from DB to Redis without changing business logic.

#### Scenario: Swap rate limit backend
- **WHEN** developer implements new `RateLimitService` with Redis backend
- **THEN** business logic code requires no changes
- **THEN** only the service instantiation changes

### Requirement: Rate limit tracking table
The system SHALL use an `ip_rate_limits` table to track request counts per IP, action type, and time window.

#### Scenario: New IP makes request
- **WHEN** IP makes first request of a type
- **THEN** system creates new record with `count = 1`, `window_start = now()`

#### Scenario: Existing IP makes request within window
- **WHEN** IP makes request within existing window
- **THEN** system increments count

#### Scenario: Window expires
- **WHEN** request comes after `window_start + 1 hour`
- **THEN** system resets count to 1, updates `window_start`

