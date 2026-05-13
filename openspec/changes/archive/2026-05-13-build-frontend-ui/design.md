## Context

The Vietnamese Legal Knowledge Graph project has backend components (contract parser, intent analyzer, retrieval pipeline, compliance analysis) built in Python but no frontend interface. This change builds a complete Next.js 14 frontend application with a distinctive hand-drawn design aesthetic to make the legal tool feel approachable and human-centered rather than corporate and intimidating.

The frontend will be a standalone application that communicates with the Python backend via REST API (SSE for streaming). During development, the frontend will use mock data since the backend is not yet complete.

## Goals / Non-Goals

**Goals:**
- Build a production-ready frontend with hand-drawn design system
- Enable user interaction with all backend capabilities (contract review, legal QA)
- Create an engaging landing page with animated walkthrough
- Support async contract review with progress tracking
- Support streaming QA responses via SSE
- Ensure full responsive design across mobile, tablet, desktop
- Maintain accessibility standards (WCAG 2.1 AA)

**Non-Goals:**
- NextAuth.js integration (deferred — placeholder auth only for now)
- Admin dashboard / system monitoring (out of scope for this change)
- Real-time collaboration features
- Mobile app (web-only, responsive)
- Backend API implementation (frontend only, with mock data)

## Decisions

### D1: Next.js 14 App Router over Pages Router
**Decision**: Use Next.js 14 App Router with React Server Components.
**Rationale**: App Router provides better performance through server components, built-in layout system for the sidebar navigation, and better SEO for the landing page. The project has no existing frontend, so there's no migration cost.
**Alternatives considered**: Pages Router (simpler but deprecated), Vite + React SPA (no SSR, worse SEO for landing page).

### D2: Custom components over shadcn/ui
**Decision**: Build all UI components from scratch with Tailwind CSS.
**Rationale**: The hand-drawn design system (wobbly borders, hard offset shadows, handwritten fonts) is fundamentally incompatible with the clean, geometric aesthetic of shadcn/ui. Customizing shadcn would require overriding nearly every style, resulting in more complexity than building from scratch.
**Alternatives considered**: shadcn/ui + heavy customization (more overhead), Radix UI primitives + custom styling (still too corporate).

### D3: Tailwind CSS for styling
**Decision**: Use Tailwind CSS as the primary styling approach.
**Rationale**: Utility-first CSS enables rapid iteration, consistent design tokens, and easy responsive design. The hand-drawn aesthetic requires many custom values (wobbly border-radius, specific shadow offsets) that are easily expressed as Tailwind utilities.
**Alternatives considered**: CSS Modules (more boilerplate), styled-components (runtime overhead, bundle size).

### D4: Framer Motion for animations
**Decision**: Use Framer Motion for all animations and transitions.
**Rationale**: Framer Motion provides declarative animation APIs that work well with React, supports scroll-triggered animations (needed for stats counters), and handles gesture-based interactions (hover, tap) cleanly.
**Alternatives considered**: CSS animations only (limited control), GSAP (heavier, overkill).

### D5: REST API with SSE for streaming
**Decision**: Use REST for all API calls, with Server-Sent Events for streaming QA responses.
**Rationale**: REST is simpler and more idiomatic for the Python backend (FastAPI). SSE provides native browser support for one-way streaming, automatic reconnection, and is lighter weight than WebSockets for the use case of streaming LLM tokens.
**Alternatives considered**: GraphQL (overkill, adds complexity), WebSockets (bidirectional, unnecessary for this use case).

### D6: Async contract review with job polling
**Decision**: Contract review uses async job pattern — upload returns job_id, client polls for status.
**Rationale**: Contract analysis can take 15-30 seconds. Async pattern allows users to navigate away and return, improving UX. Polling is simpler than WebSockets for status updates and sufficient for the expected load.
**Alternatives considered**: Sync with loading spinner (poor UX for long operations), WebSockets for real-time updates (unnecessary complexity).

### D7: Mock data layer for development
**Decision**: Build an API client layer with mock implementations that can be swapped for real endpoints.
**Rationale**: Backend is not yet complete. Mock layer allows frontend development to proceed independently. The interface contract (types, methods) will match the eventual REST API, making the swap trivial.
**Alternatives considered**: Hardcoded static data (less realistic), wait for backend (blocks progress).

### D8: Product name placeholder
**Decision**: Use "PhápLý" as the product name placeholder. Can be changed later via a single config file.
**Rationale**: Need a name for UI text, page titles, and branding. "PhápLý" is short, memorable, and relevant.

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hand-drawn aesthetic may feel unprofessional for legal tool | User trust | Balance playfulness with clear information hierarchy; keep data tables and reports clean |
| Custom components require more maintenance than UI library | Development speed | Build a comprehensive component library first; document each component |
| SSE streaming may have compatibility issues with some proxies | Reliability | Fallback to polling if SSE fails; test with common proxy configurations |
| Google Fonts (Kalam, Patrick Hand) may have slower load times | Performance | Preload fonts; use font-display: swap; consider self-hosting |
| Mock data may drift from actual API contract | Integration bugs | Define API types in a shared contract file; review with backend team before integration |
| Framer Motion adds ~15KB to bundle | Bundle size | Tree-shake unused features; lazy-load animation-heavy pages |

## Migration Plan

1. **Phase 1**: Create Next.js project with Tailwind + design tokens
2. **Phase 2**: Build UI primitive components (WobblyBox, WobblyButton, WobblyCard, etc.)
3. **Phase 3**: Build layout (AppLayout with sidebar, PublicLayout)
4. **Phase 4**: Build landing page with animated walkthrough
5. **Phase 5**: Build dashboard, contract review, and legal QA pages with mock data
6. **Phase 6**: Build settings and upgrade pages
7. **Phase 7**: Polish — animations, responsive testing, accessibility audit
8. **Phase 8**: Swap mock data for real API endpoints (when backend ready)

**Rollback**: Since this is a new frontend with no existing system to replace, rollback is simply not deploying the frontend. No data migration required.

## Open Questions

- **Q1**: What is the exact REST API contract? (endpoints, request/response schemas) — Need to align with backend team when APIs are defined.
- **Q2**: Which NextAuth.js providers will be used? (Google OAuth, email/password, both?) — Deferred to auth implementation phase.
- **Q3**: Should the landing page be a separate route group or the root `/`? — Decided: root `/` with PublicLayout.
- **Q4**: Should contract review results be downloadable as PDF? — Out of scope for MVP, can be added later.
- **Q5**: Should the chat interface support file attachments (for QA about specific documents)? — Out of scope for MVP.
