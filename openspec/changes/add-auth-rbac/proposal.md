## Why

Hiện tại PhápLý không có bất kỳ hệ thống xác thực nào. Login/register pages chỉ là UI shell, không gọi API, không quản lý session. Tất cả API calls (`api-client.ts`) không gửi auth headers. Để ship MVP production-ready với multi-tier pricing (Free/Pro/Enterprise), chúng ta cần foundation về auth, RBAC, và security ngay từ đầu.

## What Changes

- Thêm Auth.js v5 vào Next.js frontend với Google OAuth, GitHub OAuth, và Email/Password authentication
- Thiết lập Supabase Postgres làm user database (users, sessions, accounts, verification tokens)
- Hybrid session management: JWT trong httpOnly cookie + DB sessions cho revocation
- Email verification flow qua Resend
- Password reset flow
- Protected routes middleware trong Next.js
- Role-based access control (free/premium/admin) với feature gates cho contract review limits và Q&A limits
- FastAPI backend validates JWT trực tiếp qua shared secret
- Settings page thay thế mock data bằng real user profile
- Stub subscription system để tích hợp payment provider (Stripe) sau

## Capabilities

### New Capabilities

- `user-auth`: Authentication qua OAuth (Google, GitHub) và Email/Password, session management, email verification, password reset
- `authorization-rbac`: Role-based access control với 3 tiers (free/premium/admin), feature gates, rate limiting theo role
- `user-management`: User profile, settings, session management UI, account management

### Modified Capabilities

<!-- No existing capabilities are being modified. All auth/RBAC capabilities are new. -->

## Impact

- **Frontend (Next.js)**: Thêm Auth.js v5, middleware bảo vệ routes, cập nhật `api-client.ts` để gửi auth headers, thay thế mock data trong Settings page, cập nhật login/register pages với OAuth buttons
- **Backend (FastAPI)**: Thêm JWT validation dependency, role-based access checks trên protected endpoints
- **Infrastructure**: Thêm Supabase Postgres instance, Resend cho email delivery, shared JWT secret giữa Next.js và FastAPI
- **Dependencies**: Thêm `next-auth`, `@auth/supabase-adapter`, `resend`, `bcrypt`, `jose` (JWT) vào frontend; thêm `PyJWT` hoặc `python-jose` vào backend
- **Database**: Supabase schema mới (users, sessions, accounts, verificationTokens, user_roles)
