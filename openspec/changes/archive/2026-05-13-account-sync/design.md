## Context

Hiện tại hệ thống auth dùng Auth.js v5 với 3 providers: Credentials, Google, GitHub. Mỗi provider có logic tạo user riêng, không có cơ chế sync khi cùng 1 email đăng nhập bằng nhiều provider. Bảng `users` không có cột track linked providers. Name và image không được sync giữa các lần login.

## Goals / Non-Goals

**Goals:**
- 1 email = 1 user row duy nhất, bất kể provider nào
- Name và image lấy từ lần tạo account đầu tiên, giữ nguyên
- Track linked_providers (JSONB array) để biết user đã login bằng provider nào
- OAuth login với email đã có account → trỏ về user cũ, thêm provider vào linked_providers
- Register với email đã có account OAuth → cho phép đặt password cho account cũ
- OAuth-only user có thể đặt password qua forgot-password (không cần verify lại)

**Non-Goals:**
- Không có bảng accounts riêng (dùng linked_providers JSONB trong users table)
- Không có UI unlink/relink accounts (để sau)
- Không sync name/image từ provider sau khi đã có account

## Decisions

### 1. linked_providers JSONB trong users table
**Decision:** Thêm cột `linked_providers JSONB DEFAULT '[]'` vào bảng `users`.
**Rationale:** MVP đơn giản, không cần bảng accounts riêng. JSONB đủ để track providers và query được.
**Alternatives considered:**
- Bảng accounts riêng: chuẩn Auth.js nhưng phức tạp hơn, chưa cần cho MVP
- Cột boolean per provider (has_google, has_github): khó mở rộng khi thêm provider mới

### 2. Name/Image: First-write wins
**Decision:** Name và image lấy từ lần tạo account đầu tiên, giữ nguyên.
**Rationale:** Tránh override name user đã đặt. User có thể tự đổi trong settings.
**Alternatives considered:**
- Always update from latest provider: user bị mất name đã đặt
- Merge logic phức tạp: không cần thiết cho MVP

### 3. OAuth-only user đặt password qua forgot-password
**Decision:** Cho phép OAuth-only user đặt password qua forgot-password flow, không cần verify email lại.
**Rationale:** OAuth đã verified email rồi. User có thể muốn login bằng email/password sau này.
**Alternatives considered:**
- Block reset password cho OAuth user: user không thể login bằng email/password
- Yêu cầu verify lại: redundant vì OAuth đã verified

### 4. Register với email đã có account OAuth
**Decision:** Khi register với email đã có account OAuth, báo user và cho phép đặt password cho account cũ.
**Rationale:** User-friendly, không tạo account trùng. User có thể chọn login bằng OAuth hoặc đặt password.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| JSONB query chậm | MVP traffic thấp, không issue. Sau này có thể tách bảng accounts. |
| User bị confuse khi thấy name không đổi sau khi login Google | Hiển thị thông báo "Tài khoản này đã được tạo với tên X" trong settings |
| OAuth-only user đặt password → security concern nếu ai đó biết email | Forgot-password vẫn gửi link đến email, chỉ chủ email mới nhận được |
| Migration dữ liệu cũ (user đã có nhiều row cùng email) | Cleanup script: merge các row cùng email, giữ row đầu tiên |
