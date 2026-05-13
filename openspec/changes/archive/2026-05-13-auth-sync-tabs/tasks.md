## 1. AuthSyncProvider

- [x] 1.1 Create `AuthSyncProvider` component using BroadcastChannel('auth-sync') with onmessage handler for 'login', 'logout', 'session-expired' events
- [x] 1.2 Create `broadcastLogin()`, `broadcastLogout()`, `broadcastSessionExpired()` export functions
- [x] 1.3 Create `AuthExpiredModal` component with message and "Đăng nhập lại" button → redirect /login

## 2. Integration

- [x] 2.1 Wrap `AuthSyncProvider` in root `layout.tsx`
- [x] 2.2 Call `broadcastLogin()` after successful login (register, verify-otp, verify-email)
- [x] 2.3 Call `broadcastLogout()` after successful signout

## 3. Session Monitor

- [x] 3.1 Implement periodic session check (every 5 minutes) inside AuthSyncProvider
- [x] 3.2 Create 401 interceptor wrapper for fetch calls
- [x] 3.3 Broadcast 'session-expired' when session check fails or 401 detected

## 4. Testing

- [x] 4.1 Test: Tab A login → Tab B auto-unlocks content (no reload, no flash)
- [x] 4.2 Test: Tab A logout → Tab B shows modal → redirect /login
- [x] 4.3 Test: Session expired → all tabs show modal
- [x] 4.4 Test: 401 from API → session check → broadcast if expired
