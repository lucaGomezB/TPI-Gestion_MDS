---
name: Academic Excellence System
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3fd'
  on-secondary-container: '#57657b'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#0b1c30'
  on-tertiary-container: '#75859d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d5e3fd'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2f'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-lg:
    fontFamily: Source Serif 4
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Source Serif 4
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Source Serif 4
    fontSize: 28px
    fontWeight: '500'
    lineHeight: 36px
  headline-sm:
    fontFamily: Source Serif 4
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-max: 1280px
  gutter: 24px
  margin-desktop: 64px
  margin-tablet: 32px
  margin-mobile: 16px
---

## Brand & Style

This design system is built for high-level academic administration and scholarly management. The brand personality is authoritative yet accessible, embodying the quiet confidence of a prestigious institution. It prioritizes clarity and focus, stripping away ornamental distractions to center the user's attention on data and research.

The design style is a blend of **Minimalism** and **Modern Corporate**, utilizing heavy whitespace to create a sense of intellectual breathing room. The aesthetic is "New Academic"—respecting traditional scholarly values through refined typography while embracing modern efficiency through a structured, utilitarian interface. The emotional response is one of calm, control, and professional reliability.

## Colors

The palette is strictly professional, leaning on a sophisticated range of cool grays and deep blues to establish hierarchy without the need for vibrance.

- **Primary (#0F172A):** A deep Navy used for primary navigation, high-level headings, and core brand elements. It provides the grounding "anchor" for the UI.
- **Secondary (#334155):** Charcoal, used for body text and secondary interactive states to ensure high legibility and a softened contrast compared to pure black.
- **Tertiary (#64748B):** Slate Gray, reserved for de-emphasized information, captions, and decorative borders.
- **Neutral (#F8FAFC):** A soft Off-White used for the primary background. This reduces eye strain during long research sessions compared to pure white.

Avoid any use of high-saturation accents; functional colors (success, error) should be muted and integrated into this cool-toned spectrum.

## Typography

The typography strategy employs a "Serif for Thought, Sans for Action" philosophy. 

**Source Serif 4** is used for all headlines and editorial-style content. Its scholarly roots provide an immediate sense of authority and tradition. **Inter** is used for all functional UI elements, data tables, and body text. Inter’s high x-height and neutral tone ensure that dense academic data remains legible and scannable.

Text alignment should generally be flush left to maintain a strong vertical axis. For data-heavy views, use the `label-sm` style in all-caps to differentiate categories from content.

## Layout & Spacing

The design system utilizes a **Fixed Grid** for desktop views to maintain a curated, editorial feel, while transitioning to a fluid model for tablet and mobile. 

A 12-column grid is standard for desktop, with a preference for wide margins (64px) to create the "spacious" requirement of the brief. Content should often be centered with significant "dead space" on the periphery to minimize cognitive load. Vertical rhythm is strictly based on a 4px baseline, with larger sections separated by 48px or 64px increments to clearly distinguish between modules of information.

## Elevation & Depth

Hierarchy is achieved through **Tonal Layers** and extremely **Ambient Shadows**. This design system avoids heavy shadows, instead using subtle value shifts to indicate elevation.

- **Base Layer:** The Off-White (#F8FAFC) background.
- **Card Layer:** Pure White (#FFFFFF) surfaces with a 1px border of #E2E8F0 and a soft, diffused shadow (0px 4px 20px rgba(15, 23, 42, 0.04)).
- **Active Layer:** Elements that are being interacted with or require immediate attention use a slightly more pronounced shadow and a 1px border in the Primary Navy.

Avoid stacking more than two layers of depth to maintain the minimalist aesthetic.

## Shapes

The shape language is conservative and structured. A **Soft (0.25rem)** roundedness is applied to standard buttons and input fields to prevent the UI from feeling too aggressive or "sharp," while maintaining a professional, boxy silhouette. 

Cards and larger containers use `rounded-lg` (0.5rem) to provide a gentle distinction from the background. Avoid "pill" shapes or high-radius curves, as they detract from the serious, academic nature of the application.

## Components

- **Buttons:** Primary buttons are solid Navy (#0F172A) with white text. Secondary buttons use a Slate Gray outline with no fill. Padding is generous (12px 24px) to ensure a high-end feel.
- **Cards:** Refined containers with a white background and a very subtle border. Headers within cards should use `headline-sm`.
- **Data Tables:** Minimalist execution with no vertical borders. Horizontal dividers should be 1px Slate Gray at 10% opacity. Row height should be tall (56px) to maintain the spacious layout.
- **Input Fields:** Use a simple bottom-border or light 4-sided border. Labels use `label-md` and are always positioned above the field.
- **Navigation:** A clean sidebar or top-bar using the Primary color for icons and Secondary for text. Active states are indicated by a simple weight change or a subtle 2px underline/left-bar.
- **Chips:** Used for academic tags or status. These are rectangular with minimal rounding and use low-contrast background tints (e.g., #F1F5F9).