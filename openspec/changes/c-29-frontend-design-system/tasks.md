## 1. Design Tokens & Infrastructure

- [ ] 1.1 Add Google Fonts preconnect and stylesheet `<link>` tags for Source Serif 4 (wght@400,500,600) and Inter (wght@400,500,600) in `frontend/index.html`
- [ ] 1.2 Add `@import` for Google Fonts in `frontend/src/index.css` and configure Tailwind `@layer base` with `font-serif` for headlines and `font-sans` for body as the default
- [ ] 1.3 Extend `frontend/tailwind.config.ts` with design tokens: colors (primary=Navy #0F172A, secondary=Charcoal #334155, tertiary=Slate Gray #64748B, background=Off-white #F8FAFC), fontFamily (serif=Source Serif 4, sans=Inter), fontSize (headline-lg through label-sm with lineHeight, fontWeight, letterSpacing), borderRadius (sm, DEFAULT, md, lg, xl, full), boxShadow (card, card-active), spacing unit references

## 2. New Shared Components

- [ ] 2.1 Create `frontend/src/shared/components/Button.tsx` — Primary variant (solid Navy bg, white text, rounded, px-6 py-3) and Secondary variant (slate outline, transparent bg). Support `size` prop (sm/md/lg), `isLoading` state, and HTML button attributes passthrough. Write tests for both variants, loading state, and disabled state.
- [ ] 2.2 Create `frontend/src/shared/components/Card.tsx` — White bg, rounded-lg, 1px border-slate/20 (#E2E8F0), card shadow. Optional `header` and `footer` slots. Write tests for rendering children, header slot, and footer slot.
- [ ] 2.3 Create `frontend/src/shared/components/DataTable.tsx` — Typed generic component with `columns` prop (key, header, optional render/sortable/align), 56px row height, no vertical borders, horizontal dividers at 10% Slate Gray. Support loading skeleton rows, empty state message, and sortable column indicators. Write tests for column rendering, custom cell render, empty state, and loading state.
- [ ] 2.4 Create `frontend/src/shared/components/Input.tsx` — Label above with label-md styling, 4-sided light border, error state with red border and error message. Support React Hook Form integration and standard controlled usage. Write tests for rendering label, input, error message, and error styling.
- [ ] 2.5 Create `frontend/src/shared/components/Chip.tsx` — Rectangular with minimal rounding (#F1F5F9 bg, rounded), optional `onRemove` callback with X icon, text in label-sm. Write tests for render, with onRemove, and without onRemove.
- [ ] 2.6 Create `frontend/src/shared/components/Badge.tsx` — Status indicator with variants: success/green, warning/yellow, error/red, info/blue, neutral/slate. Each variant provides appropriate bg/text/ring colors. Write tests for each variant.

## 3. Existing Component Updates

- [x] 3.1 Update `frontend/src/components/Sidebar.tsx` — Change bg to Navy (#0F172A), inactive items to Secondary/Charcoal text, active state with 2px left border in Navy, section headers in label-sm all-caps, brand title in headline-sm font-serif
- [x] 3.2 Update `frontend/src/components/MainLayout.tsx` — Change bg to Off-white (#F8FAFC), header border to border-slate/20, user name section to body-md text-secondary, main content padding to px-16 lg:px-16 md:px-8 px-4
- [x] 3.3 Update `frontend/src/shared/components/PageHeader.tsx` — Title uses text-headline-lg (Source Serif 4, 40px/48px, w600, -0.02em) with responsive text-headline-lg-mobile, breadcrumbs use text-label-md, action buttons use the new Button component
- [x] 3.4 Update `frontend/src/shared/components/EmptyState.tsx` — Title uses text-headline-sm font-serif, description uses text-body-md, action button uses the new Button component
- [x] 3.5 Update `frontend/src/shared/components/Loading.tsx` — Spinner uses primary Navy colors (border-primary + border-t-primary), skeleton rows use bg-tertiary/10
- [x] 3.6 Update `frontend/src/shared/components/Modal.tsx` — Header uses text-headline-sm font-serif, apply card tokens for border (border-slate/20) and shadow (card)
- [x] 3.7 Update `frontend/src/shared/components/ErrorDisplay.tsx` — Replace blue-600 with primary Navy, apply body-md for description text
