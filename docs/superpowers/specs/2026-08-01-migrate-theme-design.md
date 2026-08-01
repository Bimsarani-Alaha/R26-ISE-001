# Migrate AI Clothes Theme into Next.js Client

## Goal

Copy the theme, styles, and fonts from
`fashoin_AI_Stylisht_frontend/AI_Clothes_Recommendation_Client/src/styles/`
into the Next.js client at `R26-ISE-001/client`, adding every style and font to
the Next.js styles.

## Source

The source client defines its design system in `src/styles/`:

- `fonts.css` — Google Fonts import for **Inter** (300, 400, 500, 600) and
  **Cormorant Garamond** (300, 400, 500, 600, italic).
- `tailwind.css` — `@import 'tailwindcss' source(none)` with an explicit
  `@source` glob, plus `@import 'tw-animate-css'`.
- `theme.css` — a shadcn-style Tailwind v4 theme:
  - `@custom-variant dark (&:is(.dark *))`
  - `:root` and `.dark` CSS variables (background, foreground, card, primary,
    secondary, muted, accent, destructive, border, input, ring, chart colors,
    sidebar colors, radius, font weights).
  - `@theme inline` block mapping the CSS variables to Tailwind tokens
    (`--color-*`, `--radius-*`).
  - `@layer base` with border/ring defaults, `body` background/foreground,
    typography for `h1`–`h4`, `label`, `button`, `input`, and a
    `.scrollbar-hide` utility.

The source also depends on `tw-animate-css` (v1.3.8), used for animations.

## Target Changes

### 1. `R26-ISE-001/client/src/app/globals.css` (replace entirely)

- `@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Inter:wght@300;400;500;600&display=swap');`
- `@import "tailwindcss";`
- `@import "tw-animate-css";`
- `@custom-variant dark (&:is(.dark *));`
- `:root` and `.dark` CSS variables copied verbatim from source `theme.css`.
- `@theme inline` block copied verbatim, plus:
  - `--font-sans: 'Inter', sans-serif;`
  - `--font-serif: 'Cormorant Garamond', serif;`
- `@layer base` copied from source `theme.css`:
  - `* { @apply border-border outline-ring/50; }`
  - `body { @apply bg-background text-foreground; font-family: 'Inter', sans-serif; }`
  - `.scrollbar-hide` utility
  - `html { font-size: var(--font-size); }`
  - Typography for `h1`–`h4`, `label`, `button`, `input`.

The source's `source(none)` + explicit `@source` is intentionally NOT copied;
Next.js auto-detects content sources with `@import "tailwindcss"`.

### 2. `R26-ISE-001/client/package.json`

Add `"tw-animate-css": "^1"` to `devDependencies` and run `npm install`.

### 3. `R26-ISE-001/client/src/app/layout.tsx`

- Remove the unused `Geist` / `Geist_Mono` `next/font/google` imports and their
  `--font-geist-sans` / `--font-geist-mono` variables (fonts now load via CSS).
- Keep the `html`/`body` structure and existing utility classes.

### 4. Existing pages (`page.tsx`, `size/page.tsx`, `about/page.tsx`)

Markup left unchanged. The custom classes (`.page-shell`, `.card`, `.hero`,
`.predict-button`, etc.) will no longer have CSS; pages render with the theme's
default styling. Restyling the pages with theme utilities is out of scope.

## Non-Goals

- No migration of the source components, routes, or pages.
- No restyling of the existing Next.js pages.
- No Tailwind config file creation (Tailwind v4 uses CSS-based config).

## Verification

- `npm run build` in `R26-ISE-001/client` completes successfully.
- The generated CSS bundle contains the theme tokens (e.g. `--color-primary`,
  `--color-sidebar`), the font import, and `tw-animate-css` output.
