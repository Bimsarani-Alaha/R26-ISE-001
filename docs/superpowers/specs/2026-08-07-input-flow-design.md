# Design: Refined Recommendation Input Flow

Date: 2026-08-07
Status: Approved (awaiting implementation)

## Summary

Refine the existing style-recommendation input flow so the customer first selects an
occasion, then describes their outfit (color, dress type, other requirements) in free
text. The existing multi-task model extracts color, usage, and article type from that
text, and the recommendation pipeline is unchanged.

Routes, the backend API, results, and detail pages are unchanged. Only the `/input`
page, the shared store, and prompt composition on `/processing` change.

## Current Behavior

- `/input` shows a required free-text box plus optional filter chips (occasion, gender,
  color preference). Submit is allowed with only free text.
- `/processing` builds a prompt from the free text plus any selected filters and calls
  `POST /predict` (`{ text }`).
- Backend returns `prediction` (color, usage, articleType) and recommendations.
- `/results` shows a grid of recommended items and an AI-analysis summary from the
  prediction.
- `/detail/[id]` shows the selected item's description, color, occasion, match reason,
  and style tips.

## Goals

- Occasion-first flow: customer picks an occasion before entering any text.
- Free-text description covers color, dress type, and other requirements.
- Model (not explicit chips) extracts color and dress type.
- Remove gender and color-preference collection (catalog is men's wear only).

## Design

### 1. Flow

- `/input` — single page, two steps with a progressive reveal. No new routes.
- `/processing` — UI unchanged; prompt composition updated.
- `/results` — unchanged.
- `/detail/[id]` — unchanged.

### 2. `/input` page restructure

**Step 1 — Occasion (required)**
- Occasion chips only: Casual, Formal, Party, Sports, Date Night, Business.
- "Continue" button is disabled until an occasion is selected.
- Clicking Continue reveals Step 2 (animated), keeping the selected occasion visible.

**Step 2 — Free text (required)**
- A single required textarea: the customer types color, dress type, and any other
  requirements in their own words.
- Example prompts provided (e.g., "A blue shirt for the office").
- "Back" link returns to Step 1.
- "Get Recommendations" is disabled until the text is non-empty.
- On submit, store the occasion and requirements, then navigate to `/processing`.

**Removed**
- Gender filter chips.
- Color preference chips.
- `colorPreference` and `gender` fields from the store.

### 3. Data flow

- `AppStoreContext`: remove `gender`/`setGender` and `colorPreference`/`setColorPreference`.
  Keep `occasion` and `requirements`.
- `processing/page.tsx`: compose the prompt as `Occasion: <occasion>. <free text>` and
  send to `/predict`. (Occasion text comes first, then the free text.)
- `recommendationApi.ts`: unchanged (`{ text }` request body).
- The extracted color and dress type come from the model's `prediction` returned by
  `/predict`; shown as the AI-analysis summary on `/results` and used in `matchReason`.

### 4. Error handling and edge cases

- Backend down: existing error card on `/processing` with "Try Again" (unchanged).
- Text with no obvious color or dress type: the model returns its best guesses; results
  remain usable.
- No free text: not possible to submit (Step 2 is required).

### 5. Testing

- Run `npm run lint` (Biome) and `npm run build` in `client/`.
- Manual checks: step gating (Continue disabled until occasion chosen), back navigation,
  prompt composition, end-to-end with the backend running if available.

## Out of Scope

- Backend/model changes.
- Changes to `/results` and `/detail/[id]` rendering.
- Catalog or dataset changes.
