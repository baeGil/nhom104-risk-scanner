## ADDED Requirements

### Requirement: Auth state syncs across tabs via BroadcastChannel
The system SHALL use BroadcastChannel API to synchronize authentication state across all tabs of the same origin. When a user logs in or logs out in one tab, all other tabs SHALL update their auth state without requiring a page reload.

#### Scenario: Login in Tab A updates Tab B
- **WHEN** user successfully logs in on Tab A
- **THEN** system broadcasts 'login' event via BroadcastChannel
- **THEN** all other tabs receive the event and fetch fresh session
- **THEN** all other tabs update auth context state and unlock protected content
- **THEN** no page reload or visual flash occurs

#### Scenario: Logout in Tab A updates Tab B
- **WHEN** user logs out on Tab A
- **THEN** system broadcasts 'logout' event via BroadcastChannel
- **THEN** all other tabs receive the event and show "Session ended" modal
- **THEN** user clicks modal button → redirects to /login

### Requirement: AuthExpiredModal for session end notifications
The system SHALL display a modal when a tab receives a logout or session expired event, informing the user that their session has ended and providing a button to redirect to the login page.

#### Scenario: Modal appears on logout broadcast
- **WHEN** tab receives 'logout' event
- **THEN** system displays AuthExpiredModal with message "Phiên đăng nhập kết thúc"
- **THEN** modal has "Đăng nhập lại" button
- **WHEN** user clicks button → system redirects to /login

#### Scenario: Modal appears on session expired
- **WHEN** tab receives 'session-expired' event
- **THEN** system displays AuthExpiredModal with message "Phiên đăng nhập đã hết hạn"
- **THEN** modal has "Đăng nhập lại" button
