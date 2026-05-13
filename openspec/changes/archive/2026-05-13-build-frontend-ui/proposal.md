## Why

The Vietnamese Legal Knowledge Graph project currently has no frontend interface. All backend components (contract parser, intent analysis, retrieval pipeline, compliance analysis) are being built as Python services with no user-facing layer. Without a frontend, users cannot interact with the system — they cannot upload contracts for review, ask legal questions, or view compliance reports. This change builds the complete frontend application to enable user interaction with all backend capabilities.

## What Changes

- **New frontend application** built with Next.js 14 (App Router) + React 18 + Tailwind CSS
- **Hand-drawn design system** with custom components (wobbly borders, handwritten typography, paper textures) — no generic UI libraries
- **Landing page** with animated walkthrough (no video), interactive demo, and pricing section
- **Contract Review UI** with async upload, progress tracking, clause visualization, and compliance reports
- **Legal QA UI** with chat interface, SSE streaming responses, intent display, and citation verification
- **Dashboard** with overview stats, recent contracts, and recent questions
- **Settings and Upgrade pages** for user preferences and pricing tiers
- **Auth placeholder** — pages exist but no gate; NextAuth.js integration deferred to later

## Capabilities

### New Capabilities

- `design-system`: Hand-drawn design tokens, custom UI primitives (WobblyBox, WobblyButton, WobblyCard, WobblyInput), decorative elements (tape, thumbtack, squiggles), and layout patterns
- `landing-page`: Public landing page with hero, animated walkthrough, features, stats, pricing, and footer
- `auth-ui`: Login and register pages with hand-drawn styling (placeholder — NextAuth.js integration deferred)
- `contract-review-ui`: File upload with drag-and-drop, async job tracking with progress visualization, clause list display, compliance report with annotations, and citation badges
- `legal-qa-ui`: Chat interface with speech bubbles, SSE streaming response display, intent tags, retrieved provision cards, and citation verification badges
- `dashboard-ui`: Overview statistics, recent contracts list, recent questions list, and quick action navigation
- `user-settings-ui`: Profile settings, API key management, preferences, and upgrade/pricing page

### Modified Capabilities

<!-- No existing specs are being modified. All frontend capabilities are new. -->

## Impact

- **New directory**: `frontend/` at project root with Next.js application
- **New dependencies**: next, react, react-dom, tailwindcss, framer-motion, lucide-react
- **Backend integration**: Frontend will consume REST API endpoints (TBD — backend not yet complete). API client layer will be built with mock data for development, swapped to real endpoints when backend is ready
- **No breaking changes**: This is a new frontend layer; existing backend code is unaffected
- **Auth deferred**: NextAuth.js integration noted as TODO; all routes open for testing during development
