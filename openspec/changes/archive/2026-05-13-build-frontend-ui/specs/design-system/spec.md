## ADDED Requirements

### Requirement: Design tokens SHALL be centralized and configurable
The design system SHALL define all visual tokens in a single source of truth (Tailwind config + CSS variables) including colors, typography, spacing, wobbly border-radius values, and hard offset shadows.

#### Scenario: Color tokens are accessible
- **WHEN** a component uses a design token color
- **THEN** it references the CSS variable (e.g., `var(--bg)`, `var(--accent)`) not a hardcoded hex value

#### Scenario: Wobbly border-radius is reusable
- **WHEN** a component needs an irregular border
- **THEN** it uses the predefined `wobbly` or `wobblyMd` radius values from config

### Requirement: Custom UI primitives SHALL replace generic UI libraries
The system SHALL provide custom-built UI components (WobblyBox, WobblyButton, WobblyCard, WobblyInput, WobblyBadge, WobblyDivider) with hand-drawn styling. No shadcn/ui, MUI, or other generic component libraries SHALL be used.

#### Scenario: WobblyButton renders with hand-drawn style
- **WHEN** a WobblyButton is rendered
- **THEN** it displays with wobbly border-radius, 3px solid border, hard offset shadow (4px 4px 0px), and Patrick Hand font

#### Scenario: WobblyButton hover state reduces shadow
- **WHEN** user hovers over a WobblyButton
- **THEN** the shadow reduces to 2px 2px 0px and the button translates 2px in both axes

#### Scenario: WobblyButton active state presses flat
- **WHEN** user clicks/activates a WobblyButton
- **THEN** the shadow disappears completely and the button translates 4px in both axes

#### Scenario: WobblyCard supports tape and tack decorations
- **WHEN** a WobblyCard is rendered with `decoration="tape"`
- **THEN** a translucent gray tape strip appears at the top with slight rotation

### Requirement: Typography SHALL use handwritten fonts exclusively
All text SHALL use Kalam (headings, weight 700) or Patrick Hand (body, weight 400) from Google Fonts. No system fonts or sans-serif fallbacks SHALL be used for primary content.

#### Scenario: Headings render in Kalam
- **WHEN** an h1-h6 element is rendered
- **THEN** it uses the Kalam font at weight 700

#### Scenario: Body text renders in Patrick Hand
- **WHEN** paragraph or small text is rendered
- **THEN** it uses the Patrick Hand font at weight 400

### Requirement: Background SHALL have paper texture
The application background SHALL display a subtle dot pattern simulating notebook paper grain using a radial gradient.

#### Scenario: Dot pattern is visible on background
- **WHEN** the app renders on any page
- **THEN** the body background shows a radial gradient dot pattern with 24px spacing

### Requirement: Decorative elements SHALL be available as reusable components
The system SHALL provide TapeStrip, Thumbtack, SquiggleSVG, ArrowSVG, and DotPattern as reusable decorative components.

#### Scenario: SquiggleSVG renders a hand-drawn connector
- **WHEN** a SquiggleSVG is placed between two elements
- **THEN** it displays a dashed, irregular curved path connecting them

### Requirement: Layout SHALL support responsive hand-drawn aesthetic
All layouts SHALL collapse to single column on mobile and expand to 2-3 columns on `md:` breakpoint. Decorative elements (arrows, bouncing shapes) SHALL be hidden on mobile.

#### Scenario: Grid collapses on mobile
- **WHEN** viewport width is below 768px
- **THEN** all multi-column grids display as single column

#### Scenario: Decorative elements hide on mobile
- **WHEN** viewport width is below 768px
- **THEN** hand-drawn arrows and bouncing decorative shapes are not displayed

### Requirement: Interactive elements SHALL have playful hover animations
Buttons, cards, and interactive elements SHALL have snappy hover animations (transition-transform duration-100) with slight rotation (rotate-1 or -rotate-2) and shadow changes.

#### Scenario: Card rotates on hover
- **WHEN** user hovers over a WobblyCard
- **THEN** it rotates by 1 degree with a 100ms transition
