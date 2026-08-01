# Size Page Restyle Design

## Goal

Restyle the pose-detection demo at `/size` to match the STYLE AI fashion site design language (white background, `#111` accents, Cormorant Garamond headings, Inter body, thin-tracked nav, motion animations), while keeping the existing functionality and backend call identical.

## Background

The `/size` page currently renders unstyled because its custom classes (`page-shell`, `card`, `hero`, `file-input-label`, `predict-button`, `measurements-card`, `measurement-row`, `height-input`, `image-card`, `info-box`) were removed when `globals.css` was replaced with the fashion theme during the prior migration. It is a pose-measurement demo that:

1. Takes a full-body photo + height in cm.
2. POSTs `multipart/form-data` (`file`, `height`) to `http://localhost:8000/predict`.
3. Shows the original and annotated result images plus a list of measurements (`shoulder_width`, `hip_width`, `height` in px; `shoulder_cm`, `hip_cm` in cm).

## Architecture

Single `"use client"` page component at `src/app/size/page.tsx`. No new files. All existing logic (state, fetch, response handling, error messages) is preserved unchanged except as noted below. Routing uses `useRouter` from `next/navigation`.

## Design

### 1. Nav

Identical to `/input`: `BACK` button (ArrowLeft icon + "BACK") calling `router.push("/")`; centered **STYLE AI** in Cormorant Garamond, `tracking-widest`, `text-[#111]`; right spacer. Container: `flex items-center justify-between px-8 md:px-16 py-6 border-b border-[#e8e8e8]`.

### 2. Header

Motion fade-up (`initial={{ opacity: 0, y: 20 }}`, `animate={{ opacity: 1, y: 0 }}`):

- Eyebrow: `POSE DETECTION` — `text-[10px] tracking-[0.3em] text-[#aaa]`, Inter.
- Heading: serif, `text-4xl md:text-5xl text-[#111] tracking-wide`, Cormorant Garamond weight 300. Copy: "Measure Your Fit".
- Subtitle: Inter, `text-sm text-[#888] tracking-wide`. Copy: "Upload a full-body photo and enter your height — our AI predicts pose measurements instantly."

### 3. Upload panel

Bordered card (`border border-[#e8e8e8]`, white background):

- Label `UPLOAD A FULL-BODY PHOTO` — `text-[10px] tracking-[0.25em] text-[#aaa]`, Inter.
- Upload area: hidden `<input type="file">` wrapped in a `<label>` styled as a bordered dashed box (`border border-[#ddd] hover:border-[#999]`, `bg-[#fafafa]`). When a file is selected, show the filename in place of the label text, plus a RESET button to clear the selection.
- Height group: `HEIGHT (CM)` label + number input. Input styled minimal (border-bottom, transparent bg, `#111` text), `placeholder="e.g. 172.5"`, `min=1 step=0.1`.
- Submit: **PREDICT IMAGE** button — `bg-[#111] text-white px-8 py-3 text-xs tracking-[0.2em]`, Inter, with ArrowUpRight icon. Disabled (`bg-[#f0f0f0] text-[#ccc] cursor-not-allowed`) until a file is selected AND height is entered. While loading, label "PROCESSING…" with a small spinner and the button disabled.
- Info/error line below the button: keeps the existing message strings (validation, backend failure, no-measurements warning), styled as muted `text-xs text-[#666]`.

### 4. Results

AnimatePresence fade-in when `preview || resultImage || measurements.length > 0`:

- Serif `RESULTS` heading.
- Two image cards side by side (`grid-cols-1 md:grid-cols-2 gap-6`), each `aspect-[3/4]` with `object-cover`, captioned `ORIGINAL` / `RESULT`, only when the corresponding data exists.
- Measurements as a bordered stat grid: one row per measurement, cells labeled `Shoulder (px)`, `Hip (px)`, `Height (px)`, `Shoulder (cm)`, `Hip (cm)` with values from the same fields as today (`m.shoulder_width`, `m.hip_width`, `m.height`, `m.shoulder_cm`, `m.hip_cm`, `?.toFixed(1)` / `?.toFixed(2)`, `?? "N/A"`).

## Data Flow

Unchanged: `handleChange` sets file/preview and clears results; `handleUpload` validates, builds `FormData`, fetches, sets `resultImage` + `measurements`, and handles the no-data and backend-error cases. Loading state toggles `loading`.

## Error Handling

Preserve the three existing `setMessage` branches with their exact copy. Reset button clears file/preview and any results/message.

## Polish / Typing

- Replace `measurements: any[]` with `interface Measurement { shoulder_width?: number; hip_width?: number; height?: number; shoulder_cm?: number; hip_cm?: number }`. This removes the pre-existing `noExplicitAny` lint on this file.
- Keep `<img>` tags (matches the rest of the site and the remote-image pattern; the `noImgElement` lint is accepted/out-of-scope).

## Verification

- `npm run build` compiles cleanly; `/size` route still present.
- `npx biome check src/app/size/page.tsx` shows no errors beyond the accepted `noImgElement` rule.
- Visual check: `/` links to `/size` via POSE DETECTION; the page matches the fashion pages' nav/typography/buttons.
