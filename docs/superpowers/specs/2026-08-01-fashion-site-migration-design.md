# Migrate Fashion AI Site into Next.js Client

## Goal

Rebuild the fashion AI clothes-recommendation site inside the Next.js client at
`R26-ISE-001/client`. The landing page is an identical recreation of the Vite
reference `HomePage.tsx`, the pose-detection demo stays untouched at `/size` and
is reachable from the homepage, the full shadcn `ui/` component library is
migrated and used to build the five fashion pages, and the `/about` page is
deleted.

## Source

`fashoin_AI_Stylisht_frontend/AI_Clothes_Recommendation_Client` (Vite + React
Router). Files to migrate:

- Pages: `src/app/pages/HomePage.tsx`, `InputPage.tsx`, `ProcessingPage.tsx`,
  `ResultsPage.tsx`, `DetailPage.tsx`.
- Components: `src/app/components/figma/ImageWithFallback.tsx` and the full
  `src/app/components/ui/*` shadcn library (45 files).
- Data: `src/app/data/recommendations.ts` (`ClothingItem`, `mockRecommendations`).
- Lib: `src/app/lib/recommendationApi.ts` (`fetchRecommendations`).
- State: `src/app/store.ts` (module-level `appStore` — replaced by Context).

The source theme (CSS variables, `@theme inline` tokens, Inter +
Cormorant Garamond fonts, `tw-animate-css`) is already migrated to the Next.js
`globals.css` in a prior task and is reused as-is.

## Target Routes (Next.js App Router)

All fashion pages are `"use client"` components.

| Path | File | Source |
|------|------|--------|
| `/` | `src/app/page.tsx` (replace) | HomePage |
| `/size` | `src/app/size/page.tsx` (keep) | existing pose detection |
| `/input` | `src/app/input/page.tsx` | InputPage |
| `/processing` | `src/app/processing/page.tsx` | ProcessingPage |
| `/results` | `src/app/results/page.tsx` | ResultsPage |
| `/detail/[id]` | `src/app/detail/[id]/page.tsx` | DetailPage |
| `/about` | **deleted** | |

## Design Decisions

### 1. HomePage (`/`)
- Visually identical to Vite `HomePage.tsx`: `STYLE AI` nav, full-screen hero
  ("LOOKS YOU REMEMBER", START NOW), feature strip, "HOW IT WORKS" section.
- Built with migrated ui components (`Button`, `Card`) using `className`
  overrides so the rendered look matches the reference pixel-for-pixel.
- Adds a **button to `/size`** (pose detection) in addition to the existing
  buttons that navigate to `/input`.

### 2. Size page (`/size`)
- Left unchanged. Only referenced via a link/button from the homepage.

### 3. Components migration
- Copy all `src/app/components/ui/*` into `src/app/components/ui/`, rewriting
  relative imports (`./utils`, `./button`, etc.) to work at the new location.
- Copy `components/figma/ImageWithFallback.tsx` into
  `src/app/components/figma/`.
- The `cn` utility (`clsx` + `tailwind-merge`) lives at
  `src/app/components/ui/utils.ts`; components import `cn` via relative paths.

### 4. Pages rebuilt with ui components
- **InputPage** — `Input`, `Textarea`, `Label`, `Button`, `Badge`
  (filter chips), keeping the Vite styling (white bg, `#111` accents, Inter /
  Cormorant, motion animations).
- **ProcessingPage** — `Progress` for the progress bar, `Card` for the steps
  checklist and style note.
- **ResultsPage** — `Card`, `Button`, `Badge` for recommendation cards,
  like button, tags.
- **DetailPage** — `Card`, `Button`, `Badge`, `Separator` for the product
  layout, color swatches, add-to-bag, related items.
- **HomePage** — `Button`, `Card`.

### 5. Shared state (React Context)
- New client provider `src/app/context/AppStoreContext.tsx` with fields:
  `requirements`, `occasion`, `gender`, `colorPreference`, `prediction`,
  `recommendations`, plus setters.
- Wrapped around children in `src/app/layout.tsx`. Replaces the source's
  mutable `appStore` imports in pages.

### 6. Data & lib
- `src/app/data/recommendations.ts` — copied verbatim.
- `src/app/lib/recommendationApi.ts` — copied, with
  `process.env.NEXT_PUBLIC_API_BASE_URL || "/api"` replacing
  `import.meta.env.VITE_API_BASE_URL`.

### 7. Routing conversion
- `useNavigate()` from `react-router` → `useRouter().push()` from
  `next/navigation`.
- `useParams()` from `react-router` → `useParams()` from `next/navigation`.
- Pages use `Link`/`router.push` for the new `/size` navigation.

### 8. Dependencies to install
- Page/runtime: `motion`, `lucide-react`.
- ui library: `clsx`, `tailwind-merge`, `class-variance-authority`, plus the
  Radix packages and libraries each ui component imports (e.g.
  `@radix-ui/react-slot`, `react-day-picker`, `date-fns`,
  `embla-carousel-react`, `recharts`, `vaul`, `sonner`,
  `react-resizable-panels`, `cmdk`, `react-hook-form`, `input-otp`, and the
  ~25 `@radix-ui/react-*` packages referenced by the ui files).
- Exact set derived from the ui components' import statements during
  implementation.

### 9. Metadata
- Update `layout.tsx` metadata title/description for the fashion app.

### 10. Verification
- `npm run build` completes (compiles + TypeScript).
- `npm run lint` shows no new errors beyond pre-existing ones in untouched
  files.

## Non-Goals

- No changes to the pose-detection page (`/size`) beyond the homepage link.
- No migration of the Vite `dist/`, routes config, or React Router specifics.
- No dark-mode restyling of the pages; the white/`#111` Vite look is preserved.

## Risks / Notes

- The ui library pulls in ~30 dependencies, most unused by the five pages, but
  required to keep the full library compileable and available for future use.
- `next/image` is not used; the reference uses `<img>` with remote Unsplash
  URLs, which is preserved.
- The `appStore` Context approach means state resets on full page reload
  (same limitation as the source).
