# Fashion AI Site Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the fashion AI site inside the Next.js client (`R26-ISE-001/client`), with an identical HomePage, a migrated shadcn `ui/` component library used to build the five fashion pages, the pose-detection demo kept at `/size` and linked from the homepage, and `/about` deleted.

**Architecture:** Next.js App Router with `"use client"` pages. Shared state via a React Context provider in the root layout. The full shadcn `ui/` library is copied into `src/app/components/ui/` and the five pages are rebuilt on top of those components (using `className` overrides to preserve the Vite look). `next/navigation` replaces `react-router`.

**Tech Stack:** Next.js 16.2.4 (App Router, Turbopack), Tailwind CSS v4, TypeScript, `motion`, `lucide-react`, Radix UI + shadcn component library.

## Global Constraints

- Do NOT modify `src/app/size/page.tsx` or the `src/app/globals.css` theme. Preserve the migrated theme, Inter + Cormorant Garamond fonts, and `tw-animate-css`.
- All five fashion pages are `"use client"` components.
- Visuals must match the Vite reference: white background, `#111` accents, Cormorant Garamond headings, Inter body, motion animations.
- API base URL: `process.env.NEXT_PUBLIC_API_BASE_URL || "/api"`.
- Routing: `useRouter()` / `useParams()` / `Link` from `next/navigation` only (no `react-router`).
- No test framework is installed in this repo; verification is `npm run build` (compiles + typechecks) and `npm run lint` (biome). Pre-existing lint errors in `page.tsx`/`size/page.tsx` are out of scope.
- Do NOT commit or stage anything unless the user explicitly asks.

**Source files (read-only reference):** `fashoin_AI_Stylisht_frontend/AI_Clothes_Recommendation_Client/src/app/{pages,components,data,lib,store.ts}`

---

### Task 1: Install dependencies

**Files:**
- Modify: `R26-ISE-001/client/package.json`

- [ ] **Step 1: Add dependencies**

Run in `R26-ISE-001/client`:
```bash
npm install motion lucide-react clsx tailwind-merge class-variance-authority cmdk input-otp next-themes react-day-picker react-resizable-panels recharts sonner vaul embla-carousel-react react-hook-form date-fns @radix-ui/react-accordion @radix-ui/react-alert-dialog @radix-ui/react-aspect-ratio @radix-ui/react-avatar @radix-ui/react-checkbox @radix-ui/react-collapsible @radix-ui/react-context-menu @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-hover-card @radix-ui/react-label @radix-ui/react-menubar @radix-ui/react-navigation-menu @radix-ui/react-popover @radix-ui/react-progress @radix-ui/react-radio-group @radix-ui/react-scroll-area @radix-ui/react-select @radix-ui/react-separator @radix-ui/react-slider @radix-ui/react-slot @radix-ui/react-switch @radix-ui/react-tabs @radix-ui/react-toggle @radix-ui/react-toggle-group @radix-ui/react-tooltip
```
Expected: installs complete; `motion`, `lucide-react`, `clsx`, `tailwind-merge`, `class-variance-authority` present in `package.json` dependencies.

- [ ] **Step 2: Verify**

Run: `node -e "const p=require('./package.json'); console.log(p.dependencies['motion'], p.dependencies['lucide-react'], p.dependencies['@radix-ui/react-slot'])"`
Expected: prints three package versions.

---

### Task 2: Migrate data + lib

**Files:**
- Create: `src/app/data/recommendations.ts`
- Create: `src/app/lib/recommendationApi.ts`

**Interfaces:**
- Produces: `interface ClothingItem` with fields `id, name, category, description, matchReason, image, price, rating, tags, styleTips, colors, material, occasion, weather`; `const mockRecommendations: ClothingItem[]`.
- Produces: `interface BackendPrediction { color; usage; articleType }`; `interface RecommendationResponse { prediction: BackendPrediction; recommendations: ClothingItem[] }`; `fetchRecommendations(text: string): Promise<RecommendationResponse>`.

- [ ] **Step 1: Copy data file verbatim**

Copy `fashoin_AI_Stylisht_frontend/AI_Clothes_Recommendation_Client/src/app/data/recommendations.ts` to `src/app/data/recommendations.ts` verbatim.

- [ ] **Step 2: Copy lib file, replace env var**

Copy the source `lib/recommendationApi.ts`, changing only:
```ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
```
in place of `import.meta.env.VITE_API_BASE_URL || "/api"`.

- [ ] **Step 3: Verify**

Run: `npx tsc --noEmit -p tsconfig.json` (from `R26-ISE-001/client`).
Expected: no errors referencing these two new files.

---

### Task 3: Migrate the shadcn `ui/` component library

**Files:**
- Create: `src/app/components/ui/` — copy all 47 files from `fashoin_AI_Stylisht_frontend/AI_Clothes_Recommendation_Client/src/app/components/ui/`
- Create: `src/app/components/figma/ImageWithFallback.tsx` (copy verbatim)

**Interfaces:**
- Produces: `cn(...inputs): string` in `src/app/components/ui/utils.ts` (clsx + tailwind-merge); `Button`, `Card`, `Input`, `Textarea`, `Label`, `Badge`, `Progress`, `Separator`, `Skeleton` (used by pages). Relative imports (`./utils`, `./button`) already resolve inside the same folder.

- [ ] **Step 1: Copy all ui files**

Copy every file from source `components/ui/` into `src/app/components/ui/` verbatim. Their relative imports (`import { cn } from "./utils"`, `import { Button } from "./button"`, etc.) work unchanged since the folder structure is identical.

- [ ] **Step 2: Copy figma component**

Copy `components/figma/ImageWithFallback.tsx` → `src/app/components/figma/ImageWithFallback.tsx` verbatim.

- [ ] **Step 3: Verify compile**

Run: `npx tsc --noEmit -p tsconfig.json`
Expected: no errors. If a ui file imports a package not installed (e.g. `date-fns`, `embla-carousel-react`), install it: `npm install <pkg>` and rerun.

---

### Task 4: Create the App Store Context

**Files:**
- Create: `src/app/context/AppStoreContext.tsx`

**Interfaces:**
- Produces: `AppStoreProvider` (client component) and hooks `useAppStore()` returning `{ requirements, occasion, gender, colorPreference, prediction, recommendations, setRequirements, setOccasion, setGender, setColorPreference, setPrediction, setRecommendations }`. Types `BackendPrediction` imported from `@/app/lib/recommendationApi` and `ClothingItem` from `@/app/data/recommendations`.

- [ ] **Step 1: Write the provider**

Create `src/app/context/AppStoreContext.tsx`:
```tsx
"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import type { BackendPrediction } from "@/app/lib/recommendationApi";
import type { ClothingItem } from "@/app/data/recommendations";

type AppStore = {
  requirements: string;
  occasion: string;
  gender: string;
  colorPreference: string;
  prediction: BackendPrediction | null;
  recommendations: ClothingItem[];
  setRequirements: (v: string) => void;
  setOccasion: (v: string) => void;
  setGender: (v: string) => void;
  setColorPreference: (v: string) => void;
  setPrediction: (v: BackendPrediction | null) => void;
  setRecommendations: (v: ClothingItem[]) => void;
};

const AppStoreContext = createContext<AppStore | null>(null);

export function AppStoreProvider({ children }: { children: ReactNode }) {
  const [requirements, setRequirements] = useState("");
  const [occasion, setOccasion] = useState("");
  const [gender, setGender] = useState("");
  const [colorPreference, setColorPreference] = useState("");
  const [prediction, setPrediction] = useState<BackendPrediction | null>(null);
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);

  return (
    <AppStoreContext.Provider
      value={{
        requirements, occasion, gender, colorPreference, prediction,
        recommendations, setRequirements, setOccasion, setGender,
        setColorPreference, setPrediction, setRecommendations,
      }}
    >
      {children}
    </AppStoreContext.Provider>
  );
}

export function useAppStore() {
  const ctx = useContext(AppStoreContext);
  if (!ctx) throw new Error("useAppStore must be used within AppStoreProvider");
  return ctx;
}
```

- [ ] **Step 2: Verify**

Run: `npx tsc --noEmit -p tsconfig.json`
Expected: no errors.

---

### Task 5: Wire provider + metadata into the root layout

**Files:**
- Modify: `src/app/layout.tsx`

- [ ] **Step 1: Wrap children in AppStoreProvider and update metadata**

Replace the imports and layout body so that `AppStoreProvider` wraps `children`, and set:
```ts
export const metadata: Metadata = {
  title: "AI Clothes Recommendation",
  description: "AI-powered outfit recommendations curated for your occasion, style, and preferences.",
};
```

- [ ] **Step 2: Verify**

Run: `npx tsc --noEmit -p tsconfig.json`
Expected: no errors.

---

### Task 6: Delete the about page

**Files:**
- Delete: `src/app/about/`

- [ ] **Step 1: Remove directory**

Delete `src/app/about/` (including `page.tsx`).

- [ ] **Step 2: Verify route removal**

Run: `npm run build` → expect no `/about` route in the route table output.

---

### Task 7: Build the HomePage at `/`

**Files:**
- Replace: `src/app/page.tsx`

**Interfaces:**
- Consumes: `useRouter` from `next/navigation`; `Button` from `@/app/components/ui/button`; `motion` from `motion/react`; `ArrowUpRight` from `lucide-react`.

- [ ] **Step 1: Recreate the HomePage**

Replace `src/app/page.tsx` with a `"use client"` component that reproduces the Vite `HomePage.tsx` structure (nav with `STYLE AI`, WOMEN/MEN/OCCASION + SKIP/LOGIN; hero with `motion.h1` "LOOKS YOU REMEMBER" and START NOW button; feature strip; HOW IT WORKS 3-step grid + GET STARTED).
- Convert `const navigate = useNavigate()` → `const router = useRouter()`; `navigate("/input")` → `router.push("/input")`.
- Render CTAs with the migrated `Button` component (`className` overrides such as `bg-white/90 text-[#111] px-7 py-3 text-xs tracking-[0.2em]` to keep the exact look).
- **Add a `/size` button:** place a second `Button` (e.g. outlined, label `POSE DETECTION`) in the nav's right-hand group AND a secondary button in the hero overlay, both calling `router.push("/size")`. Keep `Link`/`router.push` for the `/size` route.

- [ ] **Step 2: Verify build**

Run: `npm run build`
Expected: `/` route compiles; `src/app/size/page.tsx` still compiles unchanged.

---

### Task 8: Build the InputPage at `/input`

**Files:**
- Create: `src/app/input/page.tsx`

**Interfaces:**
- Consumes: `useRouter` from `next/navigation`; `useAppStore` (setters for requirements/occasion/gender/colorPreference); `Input`, `Textarea`, `Label`, `Button`, `Badge` from `@/app/components/ui/...`; `motion`; `lucide-react` icons.

- [ ] **Step 1: Recreate the InputPage**

`"use client"` component reproducing Vite `InputPage.tsx`: STEP 1 OF 2 header, main textarea (with char count + example prompts), optional filters (occasion/gender/color chips), GET RECOMMENDATIONS submit.
- Init local state from `useAppStore()` values; on submit call `setRequirements`, `setOccasion`, `setGender`, `setColorPreference`, `setPrediction(null)`, `setRecommendations([])`, then `router.push("/processing")`.
- Use `Textarea` for the description, `Button` (with custom classes) for filter chips and submit, `Badge` for the "READY ✓" indicator. Preserve the Vite styling via `className`.

- [ ] **Step 2: Verify build**

Run: `npm run build`
Expected: `/input` route compiles.

---

### Task 9: Build the ProcessingPage at `/processing`

**Files:**
- Create: `src/app/processing/page.tsx`

**Interfaces:**
- Consumes: `useRouter` from `next/navigation`; `useAppStore` (requirements, setPrediction, setRecommendations); `fetchRecommendations` from `@/app/lib/recommendationApi`; `Progress` from `@/app/components/ui/progress`; `Card` from `@/app/components/ui/card`; `motion`, `AnimatePresence`.

- [ ] **Step 1: Recreate the ProcessingPage**

`"use client"` component reproducing Vite `ProcessingPage.tsx`: spinner, "Curating Your Looks", rotating step text, progress bar, steps checklist, fashion tip, error panel.
- On mount, if `!requirements`, `router.replace("/input")`.
- Call `await fetchRecommendations(requirements)`; on success `setPrediction(result.prediction)`, `setRecommendations(result.recommendations)`, then `router.replace("/results")` after ~500ms; on error show the error panel with TRY AGAIN → `/input`.
- Use `Progress` for the progress bar and `Card` for the steps/tip/error panels, with `className` overrides preserving the Vite style.

- [ ] **Step 2: Verify build**

Run: `npm run build`
Expected: `/processing` route compiles.

---

### Task 10: Build the ResultsPage at `/results`

**Files:**
- Create: `src/app/results/page.tsx`

**Interfaces:**
- Consumes: `useRouter` from `next/navigation`; `useAppStore` (recommendations, prediction, requirements); `mockRecommendations` from `@/app/data/recommendations`; `Card`, `Button`, `Badge` from `@/app/components/ui/...`; `motion`; `lucide-react` icons (`ArrowLeft`, `ArrowUpRight`, `Star`, `Heart`, `RotateCcw`).

- [ ] **Step 1: Recreate the ResultsPage**

`"use client"` component reproducing Vite `ResultsPage.tsx`: navbar (BACK → `/input`, STYLE AI, NEW SEARCH), "Your Curated Looks" header with requirement quote + summary, recommendation grid (3/4 image, like button, category badge, title, rating, color/usage tags, VIEW MORE → `/detail/{id}`), TRY ANOTHER SEARCH.
- Source of items: `recommendations.length > 0 ? recommendations : mockRecommendations`, normalized as in the source.
- Like toggling stays local state. Use `Card` per recommendation, `Badge` for category/tags, `Button` for NEW SEARCH / TRY ANOTHER SEARCH.

- [ ] **Step 2: Verify build**

Run: `npm run build`
Expected: `/results` route compiles.

---

### Task 11: Build the DetailPage at `/detail/[id]`

**Files:**
- Create: `src/app/detail/[id]/page.tsx`

**Interfaces:**
- Consumes: `useParams` + `useRouter` from `next/navigation`; `useAppStore` (recommendations); `mockRecommendations` from `@/app/data/recommendations`; `Card`, `Button`, `Badge`, `Separator` from `@/app/components/ui/...`; `motion`; `lucide-react` icons.

- [ ] **Step 1: Recreate the DetailPage**

`"use client"` component reproducing Vite `DetailPage.tsx`: navbar (BACK TO RESULTS), image with like button + AI match badge, product info (category, name, rating stars, price + strikethrough, description, color swatches, MATERIAL/OCCASION details grid, style tips, ADD TO BAG + like), "You Might Also Like" grid.
- `const { id } = useParams()` (returns `string | string[]` in Next.js — coerce: `const itemId = Array.isArray(id) ? id[0] : id`).
- Find item from `recommendations` or `mockRecommendations`; related = others `.slice(0, 3)`.
- Use `Card`, `Button`, `Badge`, `Separator` with `className` overrides preserving the Vite look.

- [ ] **Step 2: Verify build**

Run: `npm run build`
Expected: `/detail/[id]` route compiles.

---

### Task 12: Final verification

**Files:** none

- [ ] **Step 1: Full build**

Run: `npm run build` (from `R26-ISE-001/client`)
Expected: compiles cleanly; route table shows `/`, `/size`, `/input`, `/processing`, `/results`, `/detail/[id]`, `/_not-found`; NO `/about`.

- [ ] **Step 2: Lint**

Run: `npm run lint`
Expected: no NEW errors introduced by migrated files (pre-existing errors in `page.tsx`/`size/page.tsx` are acceptable and out of scope).

- [ ] **Step 3: Sanity-check key routes**

Run `npm run dev` and confirm `/` renders the HomePage with both `/input` and `/size` buttons, `/size` still shows the pose-detection UI, and `/input` → `/processing` → `/results` → `/detail/[id]` flow navigates.
