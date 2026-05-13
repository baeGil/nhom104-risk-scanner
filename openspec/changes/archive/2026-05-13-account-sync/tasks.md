## 1. Database Migration

- [x] 1.1 Create migration script to add `linked_providers` JSONB column to `users` table with default `'[]'`
- [x] 1.2 Run migration on existing users: set `linked_providers` based on existing data (users with password_hash get `["credentials"]`, users with image from OAuth get `["google"]` or `["github"]`)

## 2. Auth.js Integration

- [x] 2.1 Modify `signIn` callback to: find user by email → if exists, return existing user + add provider to linked_providers → if not exists, create new user with linked_providers = [provider]
- [x] 2.2 Create `updateLinkedProviders(userId, provider)` function to add provider to linked_providers array (avoid duplicates)
- [x] 2.3 Ensure name and image are only set on first account creation, not updated on subsequent provider logins

## 3. Registration Flow

- [x] 3.1 Modify `/api/auth/register` to: check if email exists → if exists with OAuth provider, return error with option to set password → if exists with credentials, return "email already used"
- [x] 3.2 Add endpoint `/api/auth/set-password` for OAuth-only users to set password (requires valid reset token or current session)
- [x] 3.3 Update register UI to show "Email này đã được dùng để đăng nhập bằng Google/GitHub. Bạn có muốn đặt mật khẩu cho tài khoản này không?" với 2 options

## 4. Forgot Password Flow

- [x] 4.1 Modify `/api/auth/reset-password` to: allow OAuth-only users to receive reset link (no need to check password_hash)
- [x] 4.2 Update reset password email template to differentiate "Đặt mật khẩu lần đầu" (OAuth-only) vs "Đặt lại mật khẩu" (existing password)
- [x] 4.3 Update forgot-password UI to handle OAuth-only user case

## 5. Testing & Validation

- [x] 5.1 Test: Google login first → GitHub login same email → 1 user row, linked_providers = ["google", "github"]
- [x] 5.2 Test: Credentials registration first → Google login same email → 1 user row, name unchanged, linked_providers = ["credentials", "google"]
- [x] 5.3 Test: Google login first → Register same email → shows option to set password
- [x] 5.4 Test: OAuth-only user forgot password → sets password → can login with both Google and Credentials
- [x] 5.5 Test: Name and image not overridden by subsequent provider logins
