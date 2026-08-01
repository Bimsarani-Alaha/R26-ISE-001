# Size Page Restyle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the `/size` pose-detection page to match the STYLE AI fashion design language while keeping its existing functionality and backend call identical.

**Architecture:** Single `"use client"` page component at `src/app/size/page.tsx`. The existing state/logic (`handleChange`, `handleUpload`, loading, message strings) is preserved; only the JSX is restyled to the fashion pages' conventions (thin nav, Cormorant Garamond headings, Inter body, `#111`/white buttons, motion animations), plus a typed `Measurement` interface replaces `any[]`.

**Tech Stack:** Next.js App Router, Tailwind CSS v4, `motion`, `lucide-react`, TypeScript.

## Global Constraints

- Design spec: `R26-ISE-001/docs/superpowers/specs/2026-08-01-size-page-restyle-design.md` (approved).
- Do NOT modify `src/app/globals.css` or the theme.
- Do NOT change the backend contract: `POST http://localhost:8000/predict` with `FormData` fields `file` and `height`; response fields `annotated_image` and `measurements[]` (`shoulder_width`, `hip_width`, `height`, `shoulder_cm`, `hip_cm`).
- Keep all existing `setMessage` strings verbatim.
- Routing: `useRouter` from `next/navigation` only.
- Keep `<img>` tags (matches rest of site; `noImgElement` lint accepted/out-of-scope).
- No test framework installed; verification is `npm run build` and `npx biome check` on the file.
- Do NOT commit or stage anything unless the user explicitly asks.

---

### Task 1: Restyle the size page

**Files:**
- Modify: `R26-ISE-001/client/src/app/size/page.tsx` (full rewrite)

**Interfaces:**
- Consumes: `useRouter` from `next/navigation`; `motion` / `AnimatePresence` from `motion/react`; `ArrowLeft`, `ArrowUpRight` from `lucide-react`; `Button`, `Badge` from `@/app/components/ui/...` (optional — may use plain elements for full style fidelity).
- Produces: default-exported page component; `interface Measurement { shoulder_width?: number; hip_width?: number; height?: number; shoulder_cm?: number; hip_cm?: number }` used for the `measurements` state.

- [ ] **Step 1: Rewrite `src/app/size/page.tsx`**

Replace the entire file with the following:

```tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { ArrowLeft, ArrowUpRight } from "lucide-react";

const SERIF = { fontFamily: "'Cormorant Garamond', serif" };
const SANS = { fontFamily: "'Inter', sans-serif" };

interface Measurement {
  shoulder_width?: number;
  hip_width?: number;
  height?: number;
  shoulder_cm?: number;
  hip_cm?: number;
}

export default function SizePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [resultImage, setResultImage] = useState<string>("");
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [height, setHeight] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResultImage("");
    setMeasurements([]);
    setMessage("");
    setHeight("");
  };

  const handleReset = () => {
    setFile(null);
    setPreview("");
    setResultImage("");
    setMeasurements([]);
    setMessage("");
    setHeight("");
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select an image before predicting.");
      return;
    }

    if (!height) {
      setMessage("Please enter your height in centimeters.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("height", height);

    setLoading(true);
    setMessage("");

    try {
      const res = await fetch("http://localhost:8000/predict", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Request failed with status ${res.status}`);
      }

      const data = await res.json();

      setResultImage(data.annotated_image);
      setMeasurements(data.measurements || []);

      if (!data.measurements || data.measurements.length === 0) {
        setMessage("Prediction completed but no measurement data was returned.");
      }
    } catch (err) {
      console.error(err);
      setMessage("Error connecting to server. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const isValid = Boolean(file) && height.trim().length > 0;

  return (
    <div className="min-h-screen w-full bg-white flex flex-col">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 md:px-16 py-6 border-b border-[#e8e8e8]">
        <button
          type="button"
          onClick={() => router.push("/")}
          className="flex items-center gap-2 text-[#888] hover:text-[#111] transition-colors"
          style={SANS}
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-xs tracking-[0.1em]">BACK</span>
        </button>
        <span
          className="text-xl tracking-widest text-[#111]"
          style={{ ...SERIF, fontWeight: 300, letterSpacing: "0.3em" }}
        >
          STYLE AI
        </span>
        <div className="w-16" />
      </nav>

      {/* Content */}
      <div className="flex-1 max-w-2xl mx-auto w-full px-6 py-14">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12 text-center"
        >
          <p
            className="text-xs tracking-[0.3em] text-[#aaa] mb-4"
            style={SANS}
          >
            POSE DETECTION
          </p>
          <h1
            className="text-4xl md:text-5xl text-[#111] tracking-wide mb-4"
            style={{ ...SERIF, fontWeight: 300 }}
          >
            Measure Your Fit
          </h1>
          <p className="text-sm text-[#888] tracking-wide" style={SANS}>
            Upload a full-body photo and enter your height — our AI predicts pose
            measurements instantly.
          </p>
        </motion.div>

        {/* Upload panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="border border-[#e8e8e8] p-8 md:p-10 mb-8"
        >
          <label
            className="block text-[10px] tracking-[0.25em] text-[#aaa] mb-4"
            style={SANS}
          >
            UPLOAD A FULL-BODY PHOTO
          </label>

          <label
            className={`flex flex-col items-center justify-center border border-dashed px-6 py-10 text-center cursor-pointer transition-all duration-200 mb-6 ${
              file
                ? "border-[#111] bg-[#fafafa]"
                : "border-[#ddd] hover:border-[#999] hover:bg-[#fafafa]"
            }`}
            style={SANS}
          >
            <input
              type="file"
              accept="image/*"
              onChange={handleChange}
              className="hidden"
            />
            {file ? (
              <span className="text-xs text-[#555] break-all px-2">
                {file.name}
              </span>
            ) : (
              <>
                <span className="text-2xl text-[#ccc] mb-2">⊹</span>
                <span className="text-xs tracking-[0.15em] text-[#888]">
                  CLICK TO SELECT
                </span>
              </>
            )}
          </label>

          {file && (
            <div className="flex justify-end -mt-4 mb-6">
              <button
                type="button"
                onClick={handleReset}
                className="text-[10px] tracking-[0.15em] text-[#888] hover:text-[#111] underline underline-offset-2 transition-colors"
                style={SANS}
              >
                RESET
              </button>
            </div>
          )}

          <div className="mb-6">
            <label
              htmlFor="height"
              className="block text-[10px] tracking-[0.25em] text-[#aaa] mb-3"
              style={SANS}
            >
              HEIGHT (CM)
            </label>
            <input
              id="height"
              type="number"
              min="1"
              step="0.1"
              placeholder="e.g. 172.5"
              value={height}
              onChange={(e) => setHeight(e.target.value)}
              className="w-full bg-transparent text-[#111] placeholder-[#ccc] border-b border-[#ddd] focus:border-[#111] px-1 py-2 text-sm outline-none transition-colors duration-200"
              style={SANS}
            />
          </div>

          <button
            type="button"
            onClick={handleUpload}
            disabled={!isValid || loading}
            className={`w-full py-4 text-xs tracking-[0.25em] flex items-center justify-center gap-3 transition-all duration-300 ${
              isValid && !loading
                ? "bg-[#111] text-white hover:bg-[#333] active:scale-[0.98]"
                : "bg-[#f0f0f0] text-[#ccc] cursor-not-allowed"
            }`}
            style={SANS}
          >
            {loading ? (
              <>
                <span className="w-3.5 h-3.5 border border-[#999] border-t-transparent rounded-full animate-spin" />
                PROCESSING…
              </>
            ) : (
              <>
                PREDICT IMAGE
                <ArrowUpRight className="w-4 h-4" />
              </>
            )}
          </button>

          {message && (
            <p
              className="mt-4 text-xs text-[#666] tracking-wide"
              style={SANS}
            >
              {message}
            </p>
          )}
        </motion.div>

        {/* Results */}
        <AnimatePresence>
          {(preview || resultImage || measurements.length > 0) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.5 }}
            >
              <h2
                className="text-2xl text-[#111] tracking-wide mb-6"
                style={{ ...SERIF, fontWeight: 300 }}
              >
                Results
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {preview && (
                  <div>
                    <p
                      className="text-[10px] tracking-[0.2em] text-[#aaa] mb-3"
                      style={SANS}
                    >
                      ORIGINAL
                    </p>
                    <div className="relative aspect-[3/4] overflow-hidden bg-[#f5f5f5] border border-[#e8e8e8]">
                      <img
                        src={preview}
                        alt="Original upload preview"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </div>
                )}

                {resultImage && (
                  <div>
                    <p
                      className="text-[10px] tracking-[0.2em] text-[#aaa] mb-3"
                      style={SANS}
                    >
                      RESULT
                    </p>
                    <div className="relative aspect-[3/4] overflow-hidden bg-[#f5f5f5] border border-[#e8e8e8]">
                      <img
                        src={resultImage}
                        alt="Annotated result"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </div>
                )}
              </div>

              {measurements.length > 0 && (
                <div className="border border-[#e8e8e8]">
                  <p
                    className="text-[10px] tracking-[0.25em] text-[#aaa] px-5 pt-5 pb-3"
                    style={SANS}
                  >
                    MEASUREMENTS
                  </p>
                  {measurements.map((m, i) => (
                    <div
                      key={i}
                      className="border-t border-[#e8e8e8] grid grid-cols-2 md:grid-cols-5 divide-x divide-y md:divide-y-0 divide-[#e8e8e8]"
                    >
                      {[
                        { label: "SHOULDER (PX)", value: m.shoulder_width?.toFixed(1) ?? "N/A" },
                        { label: "HIP (PX)", value: m.hip_width?.toFixed(1) ?? "N/A" },
                        { label: "HEIGHT (PX)", value: m.height?.toFixed(1) ?? "N/A" },
                        { label: "SHOULDER (CM)", value: m.shoulder_cm?.toFixed(2) ?? "N/A" },
                        { label: "HIP (CM)", value: m.hip_cm?.toFixed(2) ?? "N/A" },
                      ].map((cell) => (
                        <div key={cell.label} className="p-4">
                          <p
                            className="text-[9px] tracking-[0.2em] text-[#aaa] mb-1.5"
                            style={SANS}
                          >
                            {cell.label}
                          </p>
                          <p className="text-sm text-[#555]" style={SANS}>
                            {cell.value}
                          </p>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `npm run build` (from `R26-ISE-001/client`)
Expected: compiles cleanly; `/size` route still present and static.

- [ ] **Step 3: Verify lint on the file**

Run: `npx biome check src/app/size/page.tsx`
Expected: no errors other than the accepted `noImgElement` rule (2 hits, one per `<img>`).

---

### Task 2: Final verification

**Files:** none

- [ ] **Step 1: Full build**

Run: `npm run build` (from `R26-ISE-001/client`)
Expected: all routes compile; route table shows `/`, `/_not-found`, `/detail/[id]`, `/input`, `/processing`, `/results`, `/size`.

- [ ] **Step 2: Sanity-check route**

Run `npm run dev`, then confirm `/` renders the POSE DETECTION button linking to `/size`, and `/size` renders the restyled page (nav, "Measure Your Fit", upload panel).
