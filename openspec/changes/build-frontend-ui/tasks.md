## 1. Project Setup

- [x] 1.1 Initialize Next.js 14 project with App Router in `frontend/` directory
- [x] 1.2 Configure Tailwind CSS with custom design tokens (colors, wobbly borders, shadows)
- [x] 1.3 Set up Google Fonts (Kalam, Patrick Hand) with font-display: swap
- [x] 1.4 Configure global CSS with paper texture background and base typography
- [x] 1.5 Set up project structure: `app/`, `components/`, `lib/`, `public/`, `styles/`
- [x] 1.6 Add dependencies: framer-motion, lucide-react, clsx, tailwind-merge

## 2. Design System — UI Primitives

- [x] 2.1 Create `WobblyBox` component with irregular border-radius and hard offset shadow
- [x] 2.2 Create `WobblyButton` component (primary + secondary variants) with hover/active states
- [x] 2.3 Create `WobblyCard` component with optional tape/tack decoration props
- [x] 2.4 Create `WobblyInput` component with wobbly border and focus state (blue ring)
- [x] 2.5 Create `WobblyBadge` component (sticky-note style tags)
- [x] 2.6 Create `WobblyDivider` component (dashed/squiggly line)
- [x] 2.7 Create `TapeStrip` decorative component
- [x] 2.8 Create `Thumbtack` decorative component
- [x] 2.9 Create `SquiggleSVG` decorative connector component
- [x] 2.10 Create `ArrowSVG` pointing arrow component
- [x] 2.11 Create `DotPattern` background texture component
- [x] 2.12 Create `AnimatedCounter` component for stats with scroll-triggered animation

## 3. Layout

- [x] 3.1 Create `PublicLayout` with header, main, footer for landing page
- [x] 3.2 Create `AppLayout` with sidebar navigation + header + main content area
- [x] 3.3 Create `Sidebar` component with hand-drawn navigation links and icons
- [x] 3.4 Create `AppHeader` component with user info and quick actions
- [x] 3.5 Set up root layout with font loading and global styles
- [x] 3.6 Configure route groups: `(public)` for landing, `(app)` for authenticated pages

## 4. Landing Page

- [x] 4.1 Build Hero section with animated headline, subtitle, and CTA button
- [x] 4.2 Build interactive demo zone (paste text → simulated compliance result)
- [x] 4.3 Build "How It Works" section with 3 step cards and squiggly SVG connectors
- [x] 4.4 Build Features section with 2-column card layout (Contract Review + Legal QA)
- [x] 4.5 Build Stats section with 4 animated counters (scroll-triggered)
- [x] 4.6 Build Pricing section with 3 post-it style tier cards
- [x] 4.7 Build Footer with navigation links, wavy underline hover effect
- [x] 4.8 Implement responsive layout for all landing page sections
- [x] 4.9 Add scroll-triggered animations using Framer Motion

## 5. Auth Pages (Placeholder)

- [x] 5.1 Create `/login` page with email/password form and hand-drawn styling
- [x] 5.2 Create `/register` page with name/email/password form
- [x] 5.3 Implement form validation UI (empty field errors)
- [x] 5.4 Ensure no auth gate — all routes accessible without login

## 6. Dashboard

- [x] 6.1 Create `/dashboard` page with AppLayout
- [x] 6.2 Build overview stats cards (contracts reviewed, questions asked, system health, graph coverage)
- [x] 6.3 Build recent contracts list with status badges
- [x] 6.4 Build recent questions list with domain tags
- [x] 6.5 Build quick action navigation cards
- [x] 6.6 Implement responsive layout (single column on mobile)

## 7. Contract Review UI

- [x] 7.1 Create `/contract-review` page with AppLayout
- [x] 7.2 Build `FileUpload` component with drag-and-drop zone and file picker fallback
- [x] 7.3 Implement file type validation (PDF/DOCX only, max 10MB)
- [x] 7.4 Build job progress page with animated steps (Parsing → Analyzing → Report)
- [x] 7.5 Build `ClauseList` component with sticky-note style cards and risk indicators
- [x] 7.6 Build `ComplianceReport` component with red marker annotations for violations
- [x] 7.7 Build `CitationBadge` component (VERIFIED/UNVERIFIED)
- [x] 7.8 Build job history list with status badges and date
- [x] 7.9 Implement mock API client for contract review endpoints
- [x] 7.10 Wire up upload → progress → results flow with mock data

## 8. Legal QA UI

- [x] 8.1 Create `/legal-qa` page with AppLayout
- [x] 8.2 Build `ChatBubble` component (user + AI variants with speech bubble styling)
- [x] 8.3 Build chat input area with send button
- [x] 8.4 Implement SSE client for streaming responses — simulated streaming via mock API
- [x] 8.5 Build streaming text display with typing cursor animation
- [x] 8.6 Build `IntentDisplay` component with colored domain/intent tags — integrated in ChatBubble
- [x] 8.7 Build `ProvisionCard` component for retrieved legal articles — integrated in ChatBubble
- [x] 8.8 Implement multi-turn conversation with context tracking
- [x] 8.9 Build conversation management (new conversation, history, delete)
- [x] 8.10 Implement mock API client for QA endpoints with simulated streaming
- [x] 8.11 Wire up chat flow with mock data

## 9. Settings & Upgrade

- [x] 9.1 Create `/settings` page with AppLayout
- [x] 9.2 Build profile section with editable fields
- [x] 9.3 Build API key management section (view, copy, generate)
- [x] 9.4 Build preferences section with toggle switches
- [x] 9.5 Create `/upgrade` page with pricing tier cards
- [x] 9.6 Highlight Pro tier with scale-up, yellow background, "Phổ biến" badge

## 10. Polish & Testing

- [x] 10.1 Add hover animations to all interactive elements (rotate, shadow change)
- [x] 10.2 Test responsive layout on mobile (320px), tablet (768px), desktop (1280px)
- [x] 10.3 Audit accessibility: keyboard navigation, focus indicators, ARIA labels
- [x] 10.4 Optimize font loading (preload, font-display: swap)
- [x] 10.5 Add loading states and error boundaries for all pages
- [x] 10.6 Test all navigation flows end-to-end with mock data
- [x] 10.7 Document component usage in a Storybook or internal docs
