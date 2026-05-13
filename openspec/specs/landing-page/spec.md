# landing-page Specification

## Purpose
TBD - created by archiving change build-frontend-ui. Update Purpose after archive.
## Requirements
### Requirement: Landing page SHALL display hero section with interactive demo
The landing page SHALL feature a hero section with an animated headline, subtitle, CTA button, and an interactive mini-demo where users can paste sample contract text and see a simulated compliance result.

#### Scenario: Hero renders with animated headline
- **WHEN** user visits the landing page
- **THEN** the hero displays an animated headline, subtitle, and "Thử ngay" CTA button

#### Scenario: Interactive demo shows simulated result
- **WHEN** user pastes sample text into the demo and clicks "Phân tích"
- **THEN** an animated compliance result appears with clause highlights

### Requirement: Landing page SHALL display "How It Works" section with 3 animated steps
The landing page SHALL show a 3-step process (Upload → Analyze → Report) connected by animated squiggly SVG lines.

#### Scenario: Steps display with animated connectors
- **WHEN** user scrolls to the "How It Works" section
- **THEN** 3 step cards appear with hand-drawn squiggly lines connecting them

### Requirement: Landing page SHALL display features section with 2 columns
The landing page SHALL show two feature cards: Contract Review and Legal QA, each with icon, title, description, and bullet points.

#### Scenario: Feature cards display side by side
- **WHEN** user scrolls to the Features section on desktop
- **THEN** two feature cards display side by side with hand-drawn styling

### Requirement: Landing page SHALL display animated stats counters
The landing page SHALL show 4 stat counters (12,921 docs, 900K nodes, 659K relations, 35 VB hợp nhất) that animate from 0 to target value when scrolled into view.

#### Scenario: Stats animate on scroll
- **WHEN** user scrolls to the Stats section
- **THEN** each counter animates from 0 to its target value over 2 seconds

### Requirement: Landing page SHALL display pricing section with post-it style cards
The landing page SHALL show 3 pricing tiers (Free, Pro, Team) styled as post-it notes with wobbly borders and hard offset shadows.

#### Scenario: Pricing cards display with highlighted Pro tier
- **WHEN** user scrolls to the Pricing section
- **THEN** 3 pricing cards display with the Pro card slightly scaled up and highlighted

### Requirement: Landing page SHALL include footer with hand-drawn styling
The landing page footer SHALL include navigation links, social links, and copyright text with hand-drawn typography and wavy underline decorations on links.

#### Scenario: Footer links have wavy underline on hover
- **WHEN** user hovers over a footer link
- **THEN** a wavy underline decoration appears beneath the link text

### Requirement: Landing page SHALL be fully responsive
All landing page sections SHALL adapt to mobile, tablet, and desktop viewports with appropriate layout changes.

#### Scenario: Landing page stacks on mobile
- **WHEN** viewport width is below 768px
- **THEN** all grid sections collapse to single column and decorative elements are hidden

