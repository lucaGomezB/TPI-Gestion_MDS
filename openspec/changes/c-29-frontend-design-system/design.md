## Context

The frontend (`React 18 + TypeScript + Vite + Tailwind v3`) has no design system. All styling is inline Tailwind utility classes with hardcoded values. The project already has `docs/DESIGN.md` with a complete Academic Excellence specification (Navy palette, Source Serif 4 + Inter typography, 4px baseline grid, soft shadows, minimalist data tables). The design system must be applied retroactively to existing components (Sidebar, MainLayout, PageHeader, EmptyState, Loading, Modal, ErrorDisplay) and new shared components built using the same tokens.

All C-* frontend changes (C-22 through C-28) are already archived, so this change is a retroactive visual refresh — no business logic changes.

## Goals / Non-Goals

**Goals:**
- One source of truth for colors, typography, spacing, shadows, and border-radius via Tailwind `theme.extend`
- Google Fonts integration for Source Serif 4 and Inter
- New shared components (Button, Card, DataTable, Input, Chip, Badge) using design tokens
- Existing components visually updated to match DESIGN.md
- No regressions in existing functionality

**Non-Goals:**
- No style changes to backend or API contracts
- No changes to navigation configuration (`navigation.ts`)
- No new feature pages or routes
- No dark mode support (not specified in DESIGN.md)
- No responsive breakpoint changes (existing Tailwind defaults suffice)
- No migration of existing pages to the new components (that is a follow-up change for each feature)

## Decisions

### D1. Tailwind `theme.extend` over CSS custom properties
- **Choice:** All design tokens go into `tailwind.config.ts` via `theme.extend` (colors, fontFamily, fontSize, spacing, borderRadius, boxShadow).
- **Rationale:** Tailwind's JIT engine already compiles only used utilities. Using `extend` preserves existing Tailwind defaults (responsive breakpoints, etc.) and keeps tokens accessible as utility classes everywhere. CSS custom properties would require a separate utility layer or `@apply` directives and add indirection with no benefit.
- **Alternatives considered:** CSS custom properties in `index.css` — rejected because they duplicate Tailwind config and lose autocompletion.

### D2. Font loading via CSS `@import` in `index.css`
- **Choice:** Add Google Fonts `@import` in `index.css` rather than `<link>` tags in `index.html`.
- **Rationale:** One less network request waterfall. The `@import` blocks rendering until fonts load, which provides a correct initial paint — no FOUT. Adding preconnect `<link>` tags in `index.html` for `fonts.googleapis.com` and `fonts.gstatic.com` still helps.
- **Trade-off:** Slightly slower initial render if fonts are large, mitigated by subsetting (latin-ext only).

### D3. Typography scale as Tailwind `fontSize` tokens
- **Choice:** Define `headline-lg`, `headline-md`, `headline-sm`, `body-lg`, `body-md`, `body-sm`, `label-md`, `label-sm` as named fontSize tokens with lineHeight, fontWeight, and letterSpacing baked in.
- **Rationale:** DESIGN.md already defines these as named named sizes. Named tokens are more semantic than raw size values and communicate intent (e.g., `text-headline-lg` means "this is a major page heading").
- **Usage convention:** Headlines use `font-serif` (auto-assigned by the token), body uses `font-sans`. No need to specify font family manually.

### D4. Atomic component directory pattern
- **Choice:** New components live in `frontend/src/shared/components/<ComponentName>/index.tsx` for single-file components, or `<ComponentName>.tsx` if the component is simple enough.
- **Rationale:** Matches the existing project convention (PageHeader.tsx, Modal.tsx, etc. are flat files). Only DataTable may warrant splitting into sub-files (row, cell, header) due to complexity.
- **Pattern:** Each component gets its own test file `<ComponentName>.test.tsx` colocated.

### D5. Sidebar redesign specifics
- **Choice:** Change `bg-gray-900` to `bg-primary` (Navy #0F172A), inactive items to `text-secondary` (#334155), active state to `bg-primary` with 2px left border in Primary Navy, section headers in `label-sm` all-caps.
- **Rationale:** DESIGN.md specifies "Navy for icons, Secondary for text, active state: 2px left-bar in Primary." The existing collapsible behavior and icon map remain unchanged.

### D6. PageHeader typography update
- **Choice:** Use `text-headline-lg` for the title (Source Serif 4, 40px/48px, weight 600, -0.02em), with responsive `text-headline-lg-mobile` below `lg` breakpoint. Breadcrumbs use `text-label-md`.
- **Rationale:** Matches the "Serif for Thought" principle — page titles are editorial/authoritative.

### D7. DataTable API design
- **Choice:** Minimalist component with no vertical borders, 56px row height (`h-14`), 1px horizontal dividers at 10% Slate Gray (`rgba(100,116,139,0.1)`), and a `columns` prop for typed column definitions.
- **API:**
  ```tsx
  interface Column<T> {
    key: keyof T | string;
    header: string;
    render?: (value: unknown, row: T) => ReactNode;
    sortable?: boolean;
    align?: 'left' | 'center' | 'right';
  }
  interface DataTableProps<T> {
    columns: Column<T>[];
    data: T[];
    isLoading?: boolean;
    emptyMessage?: string;
  }
  ```

### D8. Button API design
- **Choice:** Two variants (`primary` and `secondary`), optional `size` prop (`sm` | `md` | `lg`), and the existing `Action` interface from PageHeader is replaced by Button usage.
- **API:**
  ```tsx
  interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
  }
  ```
- **Primary:** bg-primary text-white hover:bg-primary/90 px-6 py-3 (12px 24px per spec)
- **Secondary:** border border-slate text-secondary bg-transparent hover:bg-slate/5 px-6 py-3

### D9. Card API design
- **Choice:** Container with white bg, `rounded-lg`, 1px `border-slate/20` (#E2E8F0), shadow `card` (0px 4px 20px rgba(15,23,42,0.04)), optional `header` and `footer` slots.
- **API:**
  ```tsx
  interface CardProps {
    header?: ReactNode;
    footer?: ReactNode;
    children: ReactNode;
    className?: string;
    padding?: boolean; // default true
  }
  ```

### D10. Input API design
- **Choice:** Uses React Hook Form `register` or standard controlled pattern. Label above with `label-md`. 4-sided light border.
- **API:**
  ```tsx
  interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label: string;
    error?: string;
  }
  ```

### D11. Chip and Badge design
- **Chip:** `<div>` with `bg-[#F1F5F9]` (low-contrast), `rounded` (0.25rem), px-3 py-1, `text-label-sm`.
- **Badge:** For status indicators. `<span>` with colored background (`bg-green-100` / `text-green-800` for success, etc.), `rounded`, px-2 py-0.5, `text-label-sm`.
- **Badge variants:** `success` | `warning` | `error` | `info` | `neutral` — mapped to a status color palette that extends M3 semantic colors.

### D12. Legacy component updates
- **EmptyState:** Title changes to `text-headline-sm font-serif`, description `text-body-md`, action button uses the new Button component.
- **Loading:** Spinner uses Navy (`border-primary` + `border-t-primary`), skeleton rows use `bg-slate/10`.
- **Modal:** Header uses `text-headline-sm font-serif`, card border/shadow tokens applied.
- **ErrorDisplay:** Similar treatment — Navy accents instead of the current blue-600.

### D13. Padding/margin tokens
- **Choice:** Add `4px` unit as a CSS `--spacing-unit` custom property for reference in `index.css`, and use Tailwind's native spacing scale (multiples of 4px) which matches the 4px baseline by default.
- **Container:** `max-w-screen-xl` (1280px) for main content areas.
- **Responsive margins:** Use `px-16 lg:px-16 md:px-8 px-4` pattern for 64px/32px/16px.

## Risks / Trade-offs

- **[Risk] Font loading delays** — Source Serif 4 is a large serif font family. If the Google Fonts CDN is slow, text will be invisible until loaded. **Mitigation:** Add `font-display: swap` as a fallback via the URL parameter, and set fallback fonts (Georgia, serif) in the base layer so text is readable immediately.
- **[Risk] "Fake it" classes in old pages** — Many existing feature pages use raw Tailwind classes like `bg-blue-600` or `text-gray-900`. These won't automatically pick up the new tokens. **Mitigation:** This change only updates shared components. A follow-up change (or per-feature changes) should migrate individual pages. Document this in the tasks.
- **[Trade-off] Tailwind `extend` vs. `prefix`** — Using `extend` means the color `primary` maps to `bg-primary`. If Tailwind ever adds a `primary` color, there would be a collision. Acceptable risk — Tailwind v3 does not define `primary`.
- **[Trade-off] Flat component files vs. directories** — For simple components (Chip, Badge, Input), a single file suffices. DataTable may grow beyond 200 LOC and should be split. Revisit if needed.

## Open Questions

- None — all decisions are covered by the existing DESIGN.md.
