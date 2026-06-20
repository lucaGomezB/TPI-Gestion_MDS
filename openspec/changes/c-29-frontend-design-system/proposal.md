## Why

The frontend currently has no centralized design system. Colors, typography, spacing, and component styles are ad-hoc (Tailwind utility classes scattered across features). The `docs/DESIGN.md` defines a complete Academic Excellence design system (Navy palette, Source Serif 4 + Inter typography, minimal card-based layout), but none of it is implemented. Without a design system, the UI is inconsistent, lacks the "New Academic" brand identity, and scales poorly as new features are added.

## What Changes

- **Design tokens** - Full Tailwind config with Navy/Charcoal/Slate/Off-white palette, custom font families (Source Serif 4 + Inter), typography scale (headline-lg through label-sm), spacing based on 4px unit, custom border-radius tokens, and card shadow
- **index.html** - Google Fonts preconnect + stylesheet links for Source Serif 4 and Inter
- **index.css** - CSS `@import` for both fonts + Tailwind base layer with font-family defaults
- **6 new shared components** - Button, Card, DataTable, Input, Chip, Badge, all using design tokens
- **Sidebar redesign** - Navy (#0F172A) background, white text, active state with 2px left-bar in Navy, Secondary (#334155) for inactive text
- **PageHeader redesign** - headline-lg (Source Serif 4, 40px/48px, weight 600, -0.02em) for titles, label-md for breadcrumbs
- **MainLayout update** - Off-white (#F8FAFC) background, 64px margins desktop / 32px tablet / 16px mobile
- **Legacy component update** - EmptyState, Loading, Modal, ErrorDisplay updated to use new design tokens

## Capabilities

### New Capabilities
- `design-system`: Centralized design tokens, typography scale, color palette, spacing system, border-radius tokens, and shadow presets as Tailwind extensions. Shared component library (Button, Card, DataTable, Input, Chip, Badge) consuming those tokens.

### Modified Capabilities
- None. Pure UI change — no business requirement changes.

## Impact

- **`frontend/tailwind.config.ts`** - Full theme extension replaced (no longer `extend: {}`)
- **`frontend/src/index.css`** - Font imports + base layer added
- **`frontend/index.html`** - Google Fonts links added
- **`frontend/src/components/Sidebar.tsx`** - Navy background, Secondary text, active left-bar styling
- **`frontend/src/components/MainLayout.tsx`** - Off-white background, updated spacing/margins
- **`frontend/src/shared/components/PageHeader.tsx`** - headline-lg typography, label-md breadcrumbs
- **`frontend/src/shared/components/EmptyState.tsx`** - Navy design tokens for title, button
- **`frontend/src/shared/components/Loading.tsx`** - Navy spinner, Secondary skeleton colors
- **`frontend/src/shared/components/Modal.tsx`** - Card design tokens for header/footer
- **`frontend/src/shared/components/ErrorDisplay.tsx`** - Navy accent colors
- **New: `frontend/src/shared/components/Button/`** - Primary/secondary variants
- **New: `frontend/src/shared/components/Card/`** - Container component
- **New: `frontend/src/shared/components/DataTable/`** - Minimalist table
- **New: `frontend/src/shared/components/Input/`** - Form input component
- **New: `frontend/src/shared/components/Chip/`** - Rectangular tag
- **New: `frontend/src/shared/components/Badge/`** - Status indicator
