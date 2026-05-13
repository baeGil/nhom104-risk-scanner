## Context

PhápLý là ứng dụng Next.js 16 + Python FastAPI với Neo4j knowledge graph. Hiện tại:
- Login/register pages là UI-only, không có auth logic
- `api-client.ts` không gửi auth headers
- Settings page dùng mock data (hardcoded user "Nguyễn Văn A")
- Không có database cho users (chỉ có Neo4j cho knowledge graph)
- Docker compose chỉ có Neo4j container
- Frontend có 3 pricing tiers UI sẵn (Free/Pro/Enterprise)
- Team nhỏ, ưu tiên speed to MVP

## Goals / Non-Goals

**Goals:**
- Production-ready auth với OAuth (Google, GitHub) + Email/Password
- Hybrid session management: JWT (httpOnly cookie) + DB sessions cho revocation
- Email verification qua Resend
- RBAC với 3 roles: free, premium, admin
- FastAPI backend validates JWT trực tiếp qua shared secret
- Stub subscription system cho payment integration sau
- Protected routes + feature gates theo role

**Non-Goals:**
- Payment integration (Stripe) - stub role system, implement sau
- Zalo OAuth - evaluate sau nếu cần
- 2FA/MFA - Phase 3
- Multi-tenant/Organization support - Phase 4 nếu cần
- Advanced audit logging - Phase 3

## Decisions

### 1. Auth Framework: Auth.js v5

**Decision:** Sử dụng Auth.js v5 (NextAuth) với Supabase Postgres adapter.

**Rationale:**
- Native Next.js integration, phù hợp với stack hiện tại
- Cho phép custom UI (Wobbly design system) thay vì pre-built components như Clerk
- Full control over data, dễ migrate sau
- Free tier Supabase: 50K MAU, đủ cho MVP và scale

**Alternatives considered:**
- Clerk: Faster setup (30 min) nhưng pre-built UI clash với Wobbly design, vendor lock-in cao, $25/mo sau free tier
- Supabase Auth: Good nhưng less Next.js-native, UI components không polished bằng tự build

### 2. Database: Supabase Postgres

**Decision:** Supabase làm user database (không dùng Supabase Auth, chỉ dùng DB).

**Rationale:**
- Managed Postgres, zero ops
- Free tier: 500MB DB, 50K MAU - đủ cho hàng chục nghìn users
- Auth.js có official Supabase adapter
- Dữ liệu của mình, dễ migrate

**Schema:**
```
users
├── id (uuid, PK)
├── name (varchar)
├── email (varchar, unique)
├── email_verified (timestamp)
├── image (varchar)
├── created_at (timestamp)
├── updated_at (timestamp)

accounts (Auth.js managed)
├── id (uuid, PK)
├── user_id (uuid, FK → users)
├── type (varchar: "oauth" | "email")
├── provider (varchar: "google" | "github")
├── provider_account_id (varchar)
├── access_token, refresh_token, id_token, expires_at

sessions (Auth.js managed)
├── id (uuid, PK)
├── session_token (varchar, unique)
├── user_id (uuid, FK → users)
├── expires (timestamp)

verification_tokens (Auth.js managed)
├── identifier (varchar)
├── token (varchar, unique)
├── expires (timestamp)

user_roles
├── user_id (uuid, FK → users, PK)
├── role (enum: "free" | "premium" | "admin")
├── subscription_tier (varchar: null | "professional" | "enterprise")
├── subscription_status (varchar: null | "active" | "canceled" | "past_due")
├── subscription_ends_at (timestamp)
├── created_at (timestamp)
├── updated_at (timestamp)
```

### 3. Session Strategy: Hybrid (JWT + DB)

**Decision:** JWT trong httpOnly cookie (15min expiry) + DB session cho revocation.

**Rationale:**
- JWT: Fast, stateless validation cho API calls
- DB session: Instant revocation khi logout hoặc security event
- httpOnly cookie: XSS protection
- Refresh token rotation: Security best practice

**Flow:**
```
Login → Auth.js creates JWT + DB session
       → JWT in httpOnly cookie (15min)
       → Session token in DB

API Request → JWT validated (stateless, fast)
             → Optional: check DB session not revoked

Logout → Delete DB session → JWT still valid for ≤15min
         → Clear cookie → No new JWTs
```

### 4. FastAPI Auth: Shared JWT Secret

**Decision:** FastAPI validates JWT trực tiếp qua shared secret, không cần DB lookup.

**Rationale:**
- Stateless, fast - không cần DB call per request
- JWT payload chứa user_id và role, đủ cho authorization
- Đơn giản nhất cho MVP

**Implementation:**
```python
# FastAPI dependency
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = jwt.decode(token, AUTH_SECRET, algorithms=["HS256"])
    return User(id=payload["sub"], email=payload["email"], role=payload["role"])
```

**JWT Payload:**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "free",
  "iat": 1234567890,
  "exp": 1234568790
}
```

### 5. Email Provider: Resend

**Decision:** Resend cho email verification và password reset.

**Rationale:**
- Free tier: 3K emails/month
- Setup 5 phút
- Good deliverability cho Gmail, Yahoo, Outlook (phổ biến ở VN)
- Auth.js có built-in Resend adapter

### 6. Rate Limiting

**Decision:** Rate limiting theo role, enforced ở cả Next.js middleware và FastAPI.

| Metric | Free | Premium | Enterprise |
|--------|------|---------|------------|
| Contracts/month | 5 | Unlimited | Unlimited |
| Q&A/day | 10 | Unlimited | Unlimited |
| API calls/hour | 100 | 1000 | Custom |
| Upload size | 5MB | 25MB | 100MB |

**MVP enforcement:**
- Frontend: UI feedback (disabled buttons, counters)
- Next.js middleware: Basic rate limiting
- FastAPI: Dependency-based checks
- Phase 3: Redis for distributed rate limiting

### 7. Subscription Stub

**Decision:** Stub role system với manual admin assignment, tích hợp Stripe sau.

**Rationale:**
- Payment integration phức tạp, không cần cho MVP validation
- Admin có thể manually set role trong Supabase dashboard
- Khi ready, thêm Stripe webhook để auto-update roles
- `user_roles` table designed sẵn cho subscription fields

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auth.js v5 still beta | Breaking changes | Pin version, test thoroughly before upgrade |
| Supabase free tier limits (500MB) | Scale limit | User data tiny, won't hit until 10K+ users |
| JWT 15min window after logout | Security | Short expiry acceptable; instant cookie clear prevents new requests |
| Shared JWT secret leak | Critical | Store in env vars, rotate if compromised |
| Resend email deliverability to VN providers | UX | Test with Gmail, Yahoo, Outlook VN; fallback to SendGrid if needed |
| Over-engineering RBAC early | Velocity | Start with simple enum column, no policy engine until needed |
