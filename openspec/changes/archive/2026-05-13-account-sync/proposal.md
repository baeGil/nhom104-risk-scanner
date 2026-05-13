## Why

Hiện tại hệ thống không đồng bộ tài khoản giữa các provider (Credentials, Google, GitHub). Cùng 1 email nhưng mỗi provider tạo 1 user row riêng hoặc không sync name/image, dẫn đến: user bị phân mảnh thành nhiều account, reset password cho OAuth-only user không có ý nghĩa, và không track được user đã login bằng những provider nào. Cần cơ chế email = single identity để đảm bảo 1 email = 1 user duy nhất bất kể provider.

## What Changes

- Thêm cột `linked_providers` (JSONB) vào bảng `users` để track các provider đã liên kết
- Sửa `signIn` callback: tìm user theo email → nếu có thì trỏ về, không thì tạo mới
- Name và image lấy từ lần tạo account đầu tiên, giữ nguyên, không override từ provider sau
- Khi OAuth login với email đã có account từ Credentials → trỏ về user cũ, thêm provider vào `linked_providers`
- Khi Credentials login với email đã có account từ OAuth → trỏ về user cũ
- Khi register với email đã có account từ OAuth → báo user, cho phép đặt password cho account cũ (set `password_hash` + add `credentials` vào `linked_providers`)
- Sửa forgot-password: cho phép OAuth-only user đặt password (không cần verify email lại)
- Sửa email template reset password để phân biệt "đặt mật khẩu lần đầu" và "đặt lại mật khẩu"

## Capabilities

### New Capabilities
- `account-sync`: Cơ chế đồng bộ tài khoản theo email, 1 email = 1 user duy nhất bất kể provider
- `provider-tracking`: Track và quản lý các provider đã liên kết với tài khoản

### Modified Capabilities
- `email-otp-verification`: OAuth login không cần OTP, email đã verified từ provider
- `user-auth`: Sửa luồng login/register/reset-password để hỗ trợ account sync

## Impact

- **Database**: Thêm cột `linked_providers` vào bảng `users`
- **Backend API**: Sửa `auth.ts` signIn callback, sửa `/api/auth/register`, sửa `/api/auth/reset-password`
- **Frontend**: Sửa forgot-password UI để xử lý case OAuth-only user, sửa register UI để xử lý case email đã có account OAuth
