## Why

Hiện tại người dùng đăng ký bằng email/password có thể login ngay mà không cần xác thực email. Điều này tạo rủi ro: tài khoản spam, email giả, và không có cách nào liên hệ lại user nếu cần. Cần thêm luồng xác thực email qua OTP 6 số để đảm bảo email hợp lệ và tăng bảo mật.

## What Changes

- Thêm bảng `email_otp_codes` và `ip_rate_limits` vào Supabase
- Thêm endpoint `/api/auth/verify-otp`, `/api/auth/resend-otp`, `/api/auth/auto-login`
- Thêm trang `/verify-otp` với form 6 ô nhập mã, countdown resend, auto-tab
- Sửa `/api/auth/register` để tạo OTP, gửi email branded, redirect sang `/verify-otp`
- Sửa Auth.js `signIn` callback: từ chối login credentials nếu chưa verify email
- Giữ nguyên luồng OAuth (Google/GitHub) — không cần verify thêm
- Giữ nguyên `/verify-email` (link xác thực) — hoạt động song song với OTP
- Thêm branded email template với logo, màu brand, CTA button

## Capabilities

### New Capabilities
- `email-otp-verification`: Luồng xác thực email qua OTP 6 số, bao gồm tạo OTP, gửi email, nhập mã, verify, auto-login
- `email-rate-limiting`: Rate limiting per-IP cho OTP requests (10/hour) và registrations (3/hour)
- `email-templating`: Email template branded cho xác thực email

### Modified Capabilities
- `user-auth`: Thêm yêu cầu email_verified trước khi login bằng credentials; OAuth bypass verify

## Impact

- **Database**: Thêm 2 bảng mới (`email_otp_codes`, `ip_rate_limits`), migration script
- **Backend API**: 3 endpoint mới, sửa 1 endpoint hiện tại
- **Frontend**: 1 page mới (`/verify-otp`), sửa `/register` redirect logic
- **Auth.js**: Sửa `signIn` callback để check email_verified
- **Email service**: Template mới, gửi qua Resend
- **Security**: Hash OTP trước khi lưu DB, temp token one-time use cho auto-login
