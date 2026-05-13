## 1. Database Migration

- [x] 1.1 Create migration script `002_email_otp.sql` with `email_otp_codes` table (id, user_id, code_hash, expires, is_used, failed_count, locked_until, resend_count, last_attempt_at, last_ip, last_user_agent, created_at)
- [x] 1.2 Create migration script `003_ip_rate_limits.sql` with `ip_rate_limits` table (ip_address, action_type, count, window_start, window_duration)
- [x] 1.3 Add indexes for `email_otp_codes(user_id, is_used, expires)` and `email_otp_codes(code_hash, is_used, expires)`
- [x] 1.4 Add RLS policies for new tables (allow all via service role for dev mode)

## 2. Rate Limiting Service

- [x] 2.1 Create `RateLimitService` interface in `frontend/src/lib/rate-limit.ts` with `check(ip, action, limit)` and `record(ip, action)` methods
- [x] 2.2 Implement `SupabaseRateLimitService` using `ip_rate_limits` table
- [x] 2.3 Add unit tests for rate limit service

## 3. OTP Service

- [x] 3.1 Create `OtpService` in `frontend/src/lib/otp.ts` with methods: `generate()`, `hash(code)`, `verify(code, hash)`, `createForUser(userId)`, `validateForUser(userId, code)`
- [x] 3.2 Implement OTP hashing using SHA-256 with `AUTH_SECRET` as salt
- [x] 3.3 Implement cleanup function for expired/used OTPs (for cron job)

## 4. Email Template

- [x] 4.1 Create branded email template component in `frontend/src/lib/email-templates/verification.tsx`
- [x] 4.2 Template includes: PhápLý logo placeholder, brand colors (#2563eb), large OTP display, verification button, expiry notice, footer
- [x] 4.3 Test email rendering (send test email via Resend)

## 5. API Endpoints

- [x] 5.1 Modify `/api/auth/register` to: check IP rate limit (3/hour), create OTP, send branded email, return `{ success: true, email }` instead of auto-login
- [x] 5.2 Create `/api/auth/verify-otp` endpoint: validate code, check lock status, increment failed_count, return tempToken on success
- [x] 5.3 Create `/api/auth/resend-otp` endpoint: check cooldown (60s), invalidate old OTP, generate new one, send email, reset failed_count
- [x] 5.4 Create `/api/auth/auto-login` endpoint: validate tempToken (one-time, 2-min expiry), create session, return redirect URL
- [x] 5.5 Modify `/api/auth/verify-email` to: mark verified, invalidate OTP, auto-login or redirect to login

## 6. Frontend Pages

- [x] 6.1 Create `/verify-otp/page.tsx` with: 6-digit input form (auto-focus, auto-tab), countdown timer for resend, resend button with 60s cooldown, error/success states
- [x] 6.2 Modify `/register/page.tsx` to redirect to `/verify-otp?email=<email>` on success instead of auto-login
- [x] 6.3 Modify `/verify-email/page.tsx` to auto-login after verification (or redirect to login with success message)

## 7. Auth.js Integration

- [x] 7.1 Modify `signIn` callback in `frontend/src/auth.ts` to reject credentials login if `email_verified` is null
- [x] 7.2 Ensure OAuth providers (Google, GitHub) set `email_verified` on user creation
- [x] 7.3 Add custom error message for unverified email: "Vui lòng xác thực email trước khi đăng nhập"

## 8. Testing & Validation

- [x] 8.1 Test full flow: register → receive email → enter OTP → auto-login → dashboard
- [x] 8.2 Test rate limiting: exceed 10 OTP requests/hour from same IP
- [x] 8.3 Test lock mechanism: 5 failed OTP attempts → 15-minute lock
- [x] 8.4 Test resend cooldown: 60-second wait between resends
- [x] 8.5 Test OTP expiry: wait 10 minutes → code rejected
- [x] 8.6 Test email verification link: click link → verified → auto-login
- [x] 8.7 Test OAuth login: Google/GitHub login bypasses verification
- [x] 8.8 Test unverified login attempt: rejected with proper error message
