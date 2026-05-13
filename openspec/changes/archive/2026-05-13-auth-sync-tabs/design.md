## Context

Auth.js v5 dùng JWT cookie strategy. Mỗi tab có cookie riêng nhưng cùng domain → cùng cookie. Tuy nhiên, tab không tự động reload khi tab khác login/logout, dẫn đến auth state không đồng bộ.

## Goals / Non-Goals

**Goals:**
- Login Tab A → Tab B auto-unlock nội dung (không reload, không flash)
- Logout Tab A → Tab B hiện modal → redirect /login
- Session expired → broadcast → tất cả tab hiện modal
- Token refresh failure → broadcast → tất cả tab hiện modal
- Wrap ở root layout.tsx

**Non-Goals:**
- Không sync giữa các trình duyệt khác nhau (Chrome ↔ Safari)
- Không sync giữa các thiết bị khác nhau
- Không dùng WebSocket hay server-side push

## Decisions

### 1. BroadcastChannel API
**Decision:** Dùng BroadcastChannel để sync giữa các tab.
**Rationale:** Đơn giản, realtime, cùng origin, không cần server.
**Alternatives considered:**
- localStorage events: hacky hơn, không fire trên tab gốc
- Polling: wasteful, không realtime
- WebSocket: overkill, cần server infrastructure

### 2. Session refresh: router.refresh() + context update
**Decision:** Khi nhận login event, fetch session mới → update context state.
**Rationale:** Không reload page → không flash → UX mượt.
**Alternatives considered:**
- window.location.reload(): flash, UX tệ
- Full page redirect: mất state hiện tại

### 3. Modal cho logout/expired
**Decision:** Hiện modal "Phiên đăng nhập kết thúc" với nút "Đăng nhập lại".
**Rationale:** User hiểu tại sao bị logout, chủ động redirect.

### 4. Periodic check: 5 phút
**Decision:** setInterval mỗi 5 phút fetch session.
**Rationale:** Đủ responsive, không spam server.

### 5. 401 interceptor
**Decision:** Wrap fetch để bắt 401 → check session → broadcast nếu expired.
**Rationale:** Bắt trường hợp token bị revoke giữa chừng.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| BroadcastChannel không support IE11 | Không quan trọng, target modern browsers |
| Periodic check spam server | 5 phút interval, đủ cho MVP |
| Modal xuất hiện khi user đang làm việc | User hiểu, có nút dismiss + redirect |
