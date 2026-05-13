## Context

Hiện tại hệ thống auth dùng Auth.js v5 với Credentials provider, cho phép login ngay sau khi đăng ký mà không xác thực email. Database có bảng `users` với trường `email_verified` (TIMESTAMPTZ, nullable) nhưng chưa được sử dụng. Email gửi qua Resend SDK. Rate limiting chưa có.

## Goals / Non-Goals

**Goals:**
- Xác thực email bắt buộc trước khi login bằng credentials
- OTP 6 số, hash trước khi lưu DB, expire 10 phút
- Rate limiting per-IP: 10 OTP requests/hour, 3 registrations/hour
- Auto-login sau khi verify OTP thành công qua one-time temp token (expire 2 phút)
- Branded email template tạo cảm giác professional
- Giữ song song luồng link xác thực (dự phòng)
- OAuth (Google/GitHub) bypass email verify

**Non-Goals:**
- Không có browser fingerprinting (chỉ IP + UA)
- Không có bảng log audit riêng cho MVP
- Không có Redis rate limiting (DB-based, abstracted để sau này swap được)
- Không thay đổi luồng OAuth

## Decisions

### 1. OTP hashing
**Decision:** Hash OTP bằng SHA-256 với salt trước khi lưu DB.
**Rationale:** Nếu DB leak, attacker không thể đọc OTP chưa dùng. Salt dùng `AUTH_SECRET` đã có sẵn.
**Alternatives considered:**
- Plaintext: đơn giản nhưng rủi ro nếu DB leak
- bcrypt: quá chậm cho OTP (cần verify nhanh)

### 2. OTP expiry: 10 phút
**Decision:** OTP hết hạn sau 10 phút.
**Rationale:** Cân bằng giữa UX (đủ thời gian nhập) và security (không quá dài). 15 phút hơi dài cho OTP.

### 3. Rate limiting storage: DB với interface abstract
**Decision:** Dùng bảng `ip_rate_limits` trong Supabase, nhưng wrap thành `RateLimitService` interface.
**Rationale:** MVP không cần Redis, nhưng abstract để sau này swap sang Redis mà không đổi business logic.

### 4. Auto-login via one-time temp token
**Decision:** Sau verify OTP thành công, server tạo JWT ngắn hạn (2 phút, one-time use) chứa `user_id`. Client gọi `/api/auth/auto-login` với token này để tạo session.
**Rationale:** Không cần lưu password ở frontend, an toàn hơn so với gọi `signIn("credentials")` ngầm. Token one-time use, revoke ngay sau khi dùng.

### 5. Bảng `email_otp_codes` gộp hết metadata
**Decision:** `failed_count`, `locked_until`, `resend_count`, `last_attempt_at`, `last_ip`, `last_user_agent` đều trong cùng bảng.
**Rationale:** MVP đơn giản, không cần bảng log riêng. Sau này nếu cần audit thì tách ra.

### 6. Cleanup strategy
**Decision:** Cron job (hoặc Supabase pg_cron) xóa OTP `is_used = true` hoặc `expires < now() - 24h`.
**Rationale:** Tránh table phình to. 24h đủ lâu để debug nếu cần.

### 7. Email template
**Decision:** Branded HTML với màu brand (#2563eb), logo placeholder, CTA button rõ ràng.
**Rationale:** Legal-tech product cần tạo trust. Plain HTML quá casual.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| DB rate limit chậm hơn Redis | MVP traffic thấp, chấp nhận được. Abstract để swap sau. |
| Email vào spam folder | Giữ link xác thực song song với OTP. User có thể click link. |
| OTP hash collision (SHA-256) | Xác suất cực thấp (~1/2^256). Chấp nhận được. |
| Temp token leak | TTL 2 phút, one-time use, revoke ngay sau khi dùng. |
| IP rate limit chặn user chung NAT | 10 requests/hour đủ rộng cho 1 gia đình. Có thể whitelist nếu cần. |
| Supabase pg_cron không có ở free tier | Cleanup có thể chạy qua API endpoint hoặc cron job external. |
