## 1. Infrastructure Setup

- [x] 1.1 Create Supabase project and configure Postgres database
- [x] 1.2 Run Supabase auth schema migrations (users, accounts, sessions, verification_tokens tables)
- [x] 1.3 Create user_roles table with role enum and subscription fields
- [x] 1.4 Set up Resend account and configure API key in environment
- [x] 1.5 Add environment variables to .env and .env.example (AUTH_SECRET, DATABASE_URL, RESEND_KEY, GOOGLE/GOOGLE secrets, GITHUB secrets)

## 2. Auth.js v5 Setup (Next.js)

- [x] 2.1 Install dependencies: next-auth, @auth/supabase-adapter, bcrypt, jose, resend
- [x] 2.2 Create Auth.js config at `src/auth.ts` with Supabase adapter
- [x] 2.3 Configure Google OAuth provider with client ID and secret
- [x] 2.4 Configure GitHub OAuth provider with client ID and secret
- [x] 2.5 Configure Credentials provider for email/password auth
- [x] 2.6 Configure Resend email provider for verification and password reset
- [x] 2.7 Set up JWT callbacks to include user role in token payload
- [x] 2.8 Set up session callbacks to sync role from DB to session

## 3. Auth API Routes

- [x] 3.1 Create API route handler at `src/app/api/auth/[...nextauth]/route.ts`
- [x] 3.2 Create custom registration endpoint for email/password with bcrypt hashing
- [x] 3.3 Create password reset request endpoint
- [x] 3.4 Create password reset confirmation endpoint

## 4. Frontend Auth Pages

- [x] 4.1 Update login page with Google and GitHub OAuth buttons
- [x] 4.2 Update login page to call Auth.js credentials sign-in
- [x] 4.3 Update register page with email/password form and validation
- [x] 4.4 Create forgot password page
- [x] 4.5 Create email verification pending page
- [x] 4.6 Create password reset confirmation page
- [x] 4.7 Ensure all auth pages use Wobbly design system components

## 5. Protected Routes & Middleware

- [x] 5.1 Create Next.js middleware at `src/middleware.ts` for route protection
- [x] 5.2 Configure middleware to protect all /app/* routes
- [x] 5.3 Add unverified user redirect to verification prompt
- [x] 5.4 Add post-login redirect to original requested URL
- [x] 5.5 Create auth context provider (`src/lib/auth-context.tsx`) for client-side session access

## 6. API Client Auth Integration

- [x] 6.1 Update api-client.ts to include JWT in Authorization header
- [x] 6.2 Add auth token refresh logic on 401 responses
- [x] 6.3 Update api-contract.ts to work with authenticated client
- [x] 6.4 Update api-qa.ts to work with authenticated client

## 7. FastAPI Backend Auth

- [x] 7.1 Add PyJWT dependency to requirements.txt
- [x] 7.2 Create auth dependency module in Python backend (`src/auth.py`)
- [x] 7.3 Implement JWT validation with shared secret
- [x] 7.4 Create get_current_user dependency dependency that extracts user_id, email, role from JWT
- [x] 7.5 Create require_role dependency dependency for role-based endpoint protection
- [x] 7.6 Add AUTH_SECRET environment variable to backend config
- [x] 7.7 Protect contract upload endpoint with auth dependency
- [x] 7.8 Protect Q&A endpoints with auth dependency

## 8. User Profile & Settings

- [x] 8.1 Update Settings page to fetch real user data from session
- [x] 8.2 Replace mock user data ("Nguyễn Văn A") with authenticated user profile
- [x] 8.3 Add profile update functionality (name change)
- [x] 8.4 Add current plan display with usage counters
- [x] 8.5 Add logout button that properly revokes session
- [x] 8.6 Add user avatar display from OAuth provider or gravatar

## 9. RBAC Implementation

- [x] 9.1 Create role checking utility in frontend (`src/lib/role-checks.ts`)
- [x] 9.2 Implement contract upload limit check (5/month for free users)
- [x] 9.3 Implement Q&A daily limit check (10/day for free users)
- [x] 9.4 Add usage counter display in dashboard and settings
- [x] 9.5 Create upgrade prompt modal component for limit-reached scenarios
- [x] 9.6 Add role-based feature gates in frontend (premium features show upgrade prompt)
- [x] 9.7 Add role validation in FastAPI endpoints

## 10. Email Templates

- [x] 10.1 Create email verification template (Vietnamese, branded)
- [x] 10.2 Create password reset template (Vietnamese, branded)
- [x] 10.3 Configure Resend with custom from address

## 11. Testing & Security

- [x] 11.1 Test Google OAuth flow end-to-end
- [x] 11.2 Test GitHub OAuth flow end-to-end
- [x] 11.3 Test email/password registration and login
- [x] 11.4 Test email verification flow
- [x] 11.5 Test password reset flow
- [x] 11.6 Test session revocation on logout
- [x] 11.7 Test protected route redirects for unauthenticated users
- [x] 11.8 Test free tier limits (contract and Q&A)
- [x] 11.9 Test FastAPI JWT validation with shared secret
- [x] 11.10 Verify httpOnly cookie security (no XSS access to tokens)
- [x] 11.11 Test rate limiting on auth endpoints

## 12. Cleanup & Polish

- [x] 12.1 Remove mock API files if no longer needed (`mock-api-contract.ts`, `mock-api-qa.ts`)
- [x] 12.2 Update sidebar logout button to call Auth.js signOut
- [x] 12.3 Add loading states for auth operations
- [x] 12.4 Add error handling and user-friendly error messages
- [x] 12.5 Update .env.example with all new required variables

## 13. Setup Guide — User + AI Collaboration

> Các task dưới đây cần bạn (user) thực hiện trên các dịch vụ bên ngoài.
> Tôi sẽ hướng dẫn từng bước, bạn copy kết quả vào `.env`.

### 13.1 Supabase Setup

- [x] 13.1.1 **Bạn**: Truy cập https://supabase.com → Sign in → New Project
  - Project name: `phaply`
  - Database password: tạo password mạnh, **lưu lại**
  - Region: `Southeast Asia (Singapore)` (gần VN nhất)
- [x] 13.1.2 **Bạn**: Sau khi project ready, vào Settings → Database → copy **Connection string** (URI format)
  - Format: `postgresql://postgres.xxxxx:YOUR_PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres`
  - Dán vào `.env` biến `DATABASE_URL`
- [x] 13.1.3 **Bạn**: Vào Settings → API → copy **Project URL** và **anon public key**
  - Dán vào `.env` biến `NEXT_PUBLIC_SUPABASE_URL` và `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- [x] 13.1.4 **Tôi**: Tạo migration SQL cho bảng `user_roles` và chạy trong Supabase SQL Editor

### 13.2 Google OAuth Setup

- [x] 13.2.1 **Bạn**: Truy cập https://console.cloud.google.com → Tạo project mới (hoặc dùng existing)
- [x] 13.2.2 **Bạn**: Enable **Google+ API**
- [x] 13.2.3 **Bạn**: Vào Credentials → Create Credentials → OAuth 2.0 Client ID
  - Application type: **Web application**
  - Authorized JavaScript origins: `http://localhost:3000` (dev) + production URL sau
  - Authorized redirect URIs: `http://localhost:3000/api/auth/callback/google`
- [x] 13.2.4 **Bạn**: Copy **Client ID** và **Client Secret** → dán vào `.env`:
  - `AUTH_GOOGLE_ID`
  - `AUTH_GOOGLE_SECRET`

### 13.3 GitHub OAuth Setup

- [x] 13.3.1 **Bạn**: Truy cập https://github.com/settings/developers → OAuth Apps → New OAuth App
  - Application name: `PhápLý`
  - Homepage URL: `http://localhost:3000`
  - Authorization callback URL: `http://localhost:3000/api/auth/callback/github`
- [x] 13.3.2 **Bạn**: Copy **Client ID** → tạo **Client Secret** → dán vào `.env`:
  - `AUTH_GITHUB_ID`
  - `AUTH_GITHUB_SECRET`

### 13.4 Resend Email Setup

- [x] 13.4.1 **Bạn**: Truy cập https://resend.com → Sign up → API Keys
- [x] 13.4.2 **Bạn**: Create API Key → copy → dán vào `.env`:
  - `AUTH_RESEND_KEY`
- [x] 13.4.3 **Bạn**: Verify domain trong Resend (hoặc dùng `onboarding@resend.dev` cho dev)
  - Email from address → dán vào `.env`: `AUTH_FROM_EMAIL`

### 13.5 AUTH_SECRET Generation

- [x] 13.5.1 **Tôi + Bạn**: Chạy command `openssl rand -base64 32` trong terminal → copy output → dán vào `.env`:
  - `AUTH_SECRET`

### 13.6 FastAPI Backend Config

- [x] 13.6.1 **Tôi**: Thêm `AUTH_SECRET` vào `src/config.py` cho backend
- [x] 13.6.2 **Bạn**: Đảm bảo backend `.env` có cùng `AUTH_SECRET` value với frontend

### 13.7 Verification Checklist

- [x] 13.7.1 **Bạn**: Review `.env` có đầy đủ các biến sau:
  ```
  DATABASE_URL=postgresql://...
  AUTH_SECRET=<base64 string>
  AUTH_GOOGLE_ID=<from Google Console>
  AUTH_GOOGLE_SECRET=<from Google Console>
  AUTH_GITHUB_ID=<from GitHub>
  AUTH_GITHUB_SECRET=<from GitHub>
  AUTH_RESEND_KEY=<from Resend>
  AUTH_FROM_EMAIL=<verified email>
  ```
- [x] 13.7.2 **Tôi**: Tạo `.env.example` updated với tất cả biến mới
- [x] 13.7.3 **Bạn + Tôi**: Test từng OAuth provider + email flow
