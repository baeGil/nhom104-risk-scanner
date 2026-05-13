## Why

Hiện tại auth state không được đồng bộ giữa các tab cùng trình duyệt. User login ở Tab A nhưng Tab B vẫn hiển thị chưa login. User logout ở Tab A nhưng Tab B vẫn hiển thị đã login. Gây confusion và trải nghiệm không nhất quán.

## What Changes

- Tạo `AuthSyncProvider` dùng BroadcastChannel API để sync auth state realtime giữa các tab
- Broadcast login event → các tab khác fetch session → update UI (không reload, không flash)
- Broadcast logout event → các tab khác hiện modal "Phiên đăng nhập kết thúc" → redirect /login
- Periodic session check mỗi 5 phút → phát hiện session expired → broadcast
- 401 interceptor → phát hiện token revoked → broadcast
- Wrap `AuthSyncProvider` ở root `layout.tsx`

## Capabilities

### New Capabilities
- `auth-sync`: Đồng bộ auth state giữa các tab cùng trình duyệt qua BroadcastChannel
- `session-monitor`: Giám sát session expired và token refresh failure

## Impact

- **Frontend**: Tạo `AuthSyncProvider`, sửa `layout.tsx`, sửa login/logout flows để broadcast
- **API**: Thêm interceptor cho 401 responses
