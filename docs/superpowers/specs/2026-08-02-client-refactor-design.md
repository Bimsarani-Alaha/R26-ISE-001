# Client Refactor: Shared Nav, Typography, ui Cleanup, Context Memoization

## Goal

Refactor the Next.js client at `R26-ISE-001/client` for cleaner, more maintainable
code after the fashion-site migration. No visual changes: every page must look and
behave exactly as it does today. Routing (Next.js App Router, `useRouter`/`useParams`)
is already correct and is left unchanged. This pass removes duplicated navigation,
deduplicates font constants, deletes unused migrated shadcn `ui/` files, memoizes the
app-store context value, fixes a re-fetch loop in the processing page, and extracts
inline card components from the results and detail pages.

## Scope

### 1. Shared typography + navigation

- New `src/app/components/typography.ts` exporting:
  - `SERIF` and `SANS` (the `fontFamily` style objects used on every page).
  - `StyleAiWordmark` — the styled `STYLE AI` `<span>` (serif, `tracking-widest`,
    `text-xl`, `text-[#111]`, `fontWeight: 300`, `letterSpacing: "0.3em"`).
- New `src/app/components/SiteNav.tsx` covering the 5 flow pages:
  - Props: `backHref?: string`, `backLabel?: string` (default `"BACK"`),
    `right?: React.ReactNode`, `centered?: boolean`.
  - `centered` renders `justify-center` with only the wordmark (Processing).
  - Otherwise `justify-between`: back button (rendered internally when `backHref`
    is given: `<ArrowLeft>` + label, `router.push(backHref)`, exact classes from the
    current pages) + `StyleAiWordmark` + `right` slot.
  - Nav container classes are identical to today: `flex items-center justify-between
    px-8 md:px-16 py-6 border-b border-[#e8e8e8]`.
  - Pages pass `right` to preserve exact centering:
    - Input, Size: `<div className="w-16" />`
    - Detail: `<div className="w-32" />`
    - Results: its NEW SEARCH `<Button>` (exact current JSX)
- Replace per-page `<nav>` blocks and `SERIF`/`SANS` constants in
  `page.tsx`, `input/page.tsx`, `processing/page.tsx`, `results/page.tsx`,
  `detail/[id]/page.tsx`, `size/page.tsx` with the shared pieces.
- Home (`page.tsx`) keeps its bespoke left-links nav layout (WOMEN/MEN/OCCASION,
  SKIP/LOGIN/POSE DETECTION) but imports `SERIF`/`SANS`/`StyleAiWordmark` instead
  of its inline font constants and inline wordmark span.

### 2. `ui/` cleanup

- Keep (7): `badge.tsx`, `button.tsx`, `card.tsx`, `progress.tsx`,
  `separator.tsx`, `textarea.tsx`, `utils.ts`.
- Delete the other 41 files under `src/app/components/ui/` (unused; verified no
  page or kept component imports them). This includes `calendar`, `chart`, `form`,
  `sidebar`, `command`, `carousel`, `dialog`, `sonner`, `use-mobile`, etc.
- Delete the unused `src/app/components/figma/ImageWithFallback.tsx` and the now
  empty `figma/` directory.
- Kept `ui/` files are verbatim migrated and retain their existing lint state
  (no lint-fixing of verbatim shadcn code in this pass).

### 3. Context memoization + processing effect fix

- `src/app/context/AppStoreContext.tsx`: wrap the provider `value` object in
  `useMemo`, keyed on the 6 state values (`requirements`, `occasion`, `gender`,
  `colorPreference`, `prediction`, `recommendations`). Setters are stable
  (`useState`) and included in the value without being deps.
- `src/app/processing/page.tsx`: change the effect dependency from `[router, store]`
  to `[router, store.requirements]` plus the stable setters it calls
  (`setPrediction`, `setRecommendations`). Today the whole `store` object changes
  identity on every provider re-render, so the effect re-runs and re-fetches in a
  loop until the redirect fires; with a memoized context value this becomes a
  correctness issue and must be fixed in the same pass.

### 4. Card extraction

- New `src/app/components/RecommendationCard.tsx`: move `RecommendationCard`,
  `RecommendationViewModel`, `RecommendationLike`, and `normalizeRecommendation`
  from `results/page.tsx` verbatim. `results/page.tsx` imports them; the grid +
  motion wrappers stay in the page.
- New `src/app/components/RelatedItemCard.tsx`: extract the "You Might Also Like"
  card from `detail/[id]/page.tsx` verbatim (image, name, price, rating, hover
  zoom, navigation to `/detail/[id]`). The detail page imports it and maps over
  its `related` array.

### 5. Lint / warnings policy

- No new biome issues beyond the documented baseline:
  - `noImgElement` on remote Unsplash `<img>`s — intentional, unchanged.
  - Kept `ui/` files keep their migrated lint state.
- Extracted components must be as lint-clean as the pages were before
  (matching the existing authoring style, e.g. no `React.ChangeEvent` scope issues).

## Non-Goals

- No route/layout restructuring (no route groups, no shared layout).
- No `next/image` migration, no `globals.css` changes.
- No behavior, copy, styling, or layout changes to any page.
- No lint-fixing of deleted or kept verbatim `ui/` files.

## Files

| Action | Path |
|--------|------|
| add | `client/src/app/components/typography.ts` |
| add | `client/src/app/components/SiteNav.tsx` |
| add | `client/src/app/components/RecommendationCard.tsx` |
| add | `client/src/app/components/RelatedItemCard.tsx` |
| edit | `client/src/app/context/AppStoreContext.tsx` |
| edit | `client/src/app/processing/page.tsx` |
| edit | `client/src/app/page.tsx`, `input/page.tsx`, `results/page.tsx`, `detail/[id]/page.tsx`, `size/page.tsx` |
| delete | 41 unused `client/src/app/components/ui/*` files, `client/src/app/components/figma/ImageWithFallback.tsx` |

## Verification

- `npx biome check` — no new issues beyond the documented baseline.
- `npm run build` — succeeds; route table still shows `/`, `/input`, `/processing`,
  `/results`, `/detail/[id]`, `/size`.
- `npm run dev` behind `Start-Process cmd.exe /c "npm run dev > dev.log 2>&1"`;
  GET `localhost:3000` returns 200; navigate each route to confirm the nav renders
  identically and flows still work (input → processing → results → detail).
