"use client";

import { useState, useRef } from "react";
import { SANS, SERIF } from "@/app/components/typography";

type ColorInfo = {
  palette?: { hex: string; percentage: number }[] | null;
  hex: string;
  name: string;
  rgb: number[];
};

type Result = {
  top_color: ColorInfo;
  bottom_color: ColorInfo;
  delta_e: number;
  match_label: string;
  top_hard: boolean;
  bottom_hard: boolean;
  cvd_type: string;
};

const CVD_OPTIONS = ["Normal", "Protanopia", "Deuteranopia", "Tritanopia"];

const CVD_DESCRIPTIONS: Record<string, string> = {
  Normal: "Normal vision",
  Protanopia: "Protanopia",
  Deuteranopia: "Deuteranopia",
  Tritanopia: "Tritanopia",
};

const MATCH_BADGE: Record<string, { bg: string; text: string; bar: string; desc: string }> = {
  "Good match": {
    bg: "bg-[#eef4f1]",
    text: "text-[#2B6E5E]",
    bar: "#2B6E5E",
    desc: "These colours pair well together — good contrast.",
  },
  "Moderate match": {
    bg: "bg-[#faf3e4]",
    text: "text-[#9C6B1A]",
    bar: "#B4791E",
    desc: "Acceptable pairing — some contrast but not ideal.",
  },
  "Poor match": {
    bg: "bg-[#fbeeec]",
    text: "text-[#A3372E]",
    bar: "#B0453F",
    desc: "These colours are too similar or clash — consider changing one.",
  },
};

export default function ClothingMatcher() {
  const [cvdType, setCvdType] = useState("Normal");
  const [topFile, setTopFile] = useState<File | null>(null);
  const [botFile, setBotFile] = useState<File | null>(null);
  const [topPreview, setTopPreview] = useState<string>("");
  const [botPreview, setBotPreview] = useState<string>("");
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const topRef = useRef<HTMLInputElement>(null);
  const botRef = useRef<HTMLInputElement>(null);

  /**
   * handleFile
   * Stores the selected file (top or bottom) in state and generates a local
   * object URL for instant image preview. Also clears any previous result
   * or error, since a new upload invalidates the last analysis.
   */
  function handleFile(file: File, which: "top" | "bottom") {
    const url = URL.createObjectURL(file);
    if (which === "top") {
      setTopFile(file);
      setTopPreview(url);
    } else {
      setBotFile(file);
      setBotPreview(url);
    }
    setResult(null);
    setError("");
  }

  /**
   * analyse
   * Sends the uploaded top/bottom images plus the selected CVD type to the
   * backend analysis endpoint, then stores the returned Result in state.
   * Handles loading state and surfaces a friendly error if the backend
   * request fails (e.g. server not running).
   */
  async function analyse() {
    if (!topFile || !botFile) return;
    setLoading(true);
    setError("");
    setResult(null);

    const form = new FormData();
    form.append("top", topFile);
    form.append("bottom", botFile);
    form.append("cvd_type", cvdType);

    try {
      const res = await fetch("http://localhost:8000/cvdmatcher/analyse", {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error("Server error");
      const data: Result = await res.json();
      setResult(data);
    } catch {
      setError(
        "Cannot reach the backend. Make sure you started it (see README).",
      );
    } finally {
      setLoading(false);
    }
  }

  // Analyse button is only enabled once both images are uploaded and no request is in flight
  const canAnalyse = !!topFile && !!botFile && !loading;

  // Derives the gauge needle's rotation angle (in degrees) from the delta_e score,
  // mapping a 0–100 range onto a -90° to +90° semicircle sweep
  const gaugeAngle = result
    ? -90 + Math.min(100, Math.max(0, result.delta_e)) * 1.8
    : -90;

  return (
    <div
      className="w-full max-w-4xl border overflow-hidden bg-white"
      style={{ borderColor: "#e8e8e8" }}
    >
      <div className="p-8 md:p-10">
        {/* Header — full width */}
        <div className="space-y-1.5 text-center mb-8">
          {/* <span
            className="text-[10px] tracking-[0.25em] text-[#aaa]"
            style={SANS}
          >
            COLOUR VISION TOOL
          </span>
          <h1
            className="text-xl tracking-[0.1em] text-[#111]"
            style={{ ...SERIF, fontWeight: 400 }}
          >
            CVD Clothing Matcher
          </h1> */}
          <p className="text-s text-[#111]" style={{ ...SANS, fontWeight: 300 }}>
            Upload your top and bottom clothing to check how well they match.
          </p>
        </div>

        {/* Two-column layout: controls left, results right */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {/* LEFT — controls & upload */}
          <div className="space-y-7">
            {/* CVD selector — lets user choose their colour vision type, used both
                for the backend analysis and for tailoring the visibility feedback */}
            <div className="space-y-1.5">
              <label
                className="text-[10px] tracking-[0.2em] text-[#888]"
                style={SANS}
              >
                YOUR VISION TYPE
              </label>
              <div className="relative">
                <select
                  value={cvdType}
                  onChange={(e) => {
                    setCvdType(e.target.value);
                    setResult(null);
                  }}
                  className="w-full appearance-none px-3.5 py-2.5 text-sm focus:outline-none transition"
                  style={{
                    ...SANS,
                    fontWeight: 400,
                    color: "#111",
                    background: "#fafafa",
                    border: "1px solid #e8e8e8",
                  }}
                >
                  {CVD_OPTIONS.map((o) => (
                    <option key={o} value={o}>
                      {CVD_DESCRIPTIONS[o]}
                    </option>
                  ))}
                </select>
                <svg
                  className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2"
                  width="12"
                  height="12"
                  viewBox="0 0 12 12"
                  fill="none"
                >
                  <path
                    d="M2.5 4.5L6 8L9.5 4.5"
                    stroke="#999"
                    strokeWidth="1.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            </div>

            {/* Upload row — two clickable image drop zones (Top / Bottom),
                each opens a hidden file input and shows a live preview once selected */}
            <div className="space-y-1.5">
              <label
                className="text-[10px] tracking-[0.2em] text-[#888]"
                style={SANS}
              >
                UPLOAD CLOTHING IMAGES
              </label>
              <div className="grid grid-cols-2 gap-4 pt-5">
                {(["top", "bottom"] as const).map((which) => {
                  const preview = which === "top" ? topPreview : botPreview;
                  const inputRef = which === "top" ? topRef : botRef;
                  const label = which === "top" ? "Top" : "Bottom";
                  return (
                    <div key={which} className="flex flex-col gap-1.5">
                      <span
                        className="text-[10px] text-center tracking-[0.15em] text-[#111]"
                        style={SANS}
                      >
                        {label.toUpperCase()}
                      </span>
                      <button
                        type="button"
                        onClick={() => inputRef.current?.click()}
                        className="w-full h-44 transition flex flex-col items-center justify-center gap-2 overflow-hidden relative group"
                        style={{
                          border: preview ? "1px solid #e8e8e8" : "1px dashed #ccc",
                          background: preview ? "transparent" : "#fafafa",
                        }}
                      >
                        {preview ? (
                          <img
                            src={preview}
                            alt={label}
                            className="absolute inset-0 w-full h-full object-cover"
                          />
                        ) : (
                          <>
                            <svg
                              width="24"
                              height="24"
                              viewBox="0 0 24 24"
                              fill="none"
                              className="transition group-hover:opacity-60"
                            >
                              <path
                                d="M9 3L7 5H4a1 1 0 00-1 1v13a1 1 0 001 1h16a1 1 0 001-1V6a1 1 0 00-1-1h-3l-2-2H9z"
                                stroke="#999"
                                strokeWidth="1.4"
                                strokeLinejoin="round"
                              />
                              <circle cx="12" cy="13" r="3.4" stroke="#999" strokeWidth="1.4" />
                            </svg>
                            <span
                              className="text-[10px] tracking-[0.1em]"
                              style={{ ...SANS, color: "#999" }}
                            >
                              CLICK TO UPLOAD
                            </span>
                          </>
                        )}
                      </button>
                      <input
                        ref={inputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => {
                          if (e.target.files?.[0])
                            handleFile(e.target.files[0], which);
                        }}
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Analyse button — triggers the analyse() request; disabled until
                both images are present, shows a spinner while loading */}
            <button
              type="button"
              onClick={analyse}
              disabled={!canAnalyse}
              className="w-full py-3 text-xs tracking-[0.2em] transition active:scale-[0.98] disabled:cursor-not-allowed"
              style={{
                ...SANS,
                fontWeight: 400,
                background: canAnalyse ? "#111" : "#eee",
                color: canAnalyse ? "#fff" : "#aaa",
                border: canAnalyse ? "1px solid #111" : "1px solid #eee",
              }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="animate-spin h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v8z"
                    />
                  </svg>
                  ANALYSING…
                </span>
              ) : (
                "ANALYSE COLOURS →"
              )}
            </button>

            {/* Error banner — shown only if analyse() failed (e.g. backend unreachable) */}
            {error && (
              <div
                className="px-4 py-3 text-sm"
                style={{ background: "#fbeeec", border: "1px solid #f3cfcb", color: "#A3372E", ...SANS, fontWeight: 300 }}
              >
                {error}
              </div>
            )}
          </div>

          {/* RIGHT — results */}
          <div className="space-y-5">
            {!result ? (
              // Placeholder shown before any analysis has been run
              <div
                className="h-full min-h-[280px] flex items-center justify-center p-6 text-center"
                style={{ background: "#fafafa", border: "1px dashed #e0e0e0" }}
              >
                <p className="text-xs text-[#aaa]" style={{ ...SANS, fontWeight: 300 }}>
                  Upload a top and bottom, then analyse to see the colour
                  breakdown and match result here.
                </p>
              </div>
            ) : (
              <>
                {/* Identified palettes block — renders each garment's detected colour
                    palette as a row of swatches with their percentage share.
                    Falls back to a single swatch (the main hex) if no palette array exists. */}
                <div>
                  <p
                    className="text-[10px] tracking-[0.2em] text-[#888] mb-2"
                    style={SANS}
                  >
                    IDENTIFIED PALETTES
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: "Top", color: result.top_color },
                      { label: "Bottom", color: result.bottom_color },
                    ].map(({ label, color }) => (
                      <div
                        key={label}
                        className="flex flex-col items-center gap-3 p-4"
                        style={{ background: "#fafafa", border: "1px solid #e8e8e8" }}
                      >
                        <span
                          className="text-[9px] tracking-[0.15em]"
                          style={{ ...SANS, color: "#999" }}
                        >
                          {label.toUpperCase()}
                        </span>

                        <div className="flex gap-2">
                          {(color.palette && color.palette.length > 0
                            ? color.palette
                            : [{ hex: color.hex, percentage: 100 }]
                          ).map(
                            (p: { hex: string; percentage: number }, i: number) => (
                              <div
                                key={i}
                                className="flex flex-col items-center gap-1"
                              >
                                <div
                                  className="w-12 h-12"
                                  style={{
                                    background: p.hex,
                                    border: "1px solid #FFFFFF",
                                    boxShadow: "0 0 0 1px #e8e8e8",
                                  }}
                                />
                                <span
                                  className="text-[10px]"
                                  style={{ ...SANS, color: "#999" }}
                                >
                                  {p.percentage}%
                                </span>
                              </div>
                            ),
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Match result block — renders the Good/Moderate/Poor badge and a
                    semicircular Delta E gauge (arc fill + needle) driven by result.delta_e */}
                {(() => {
                  const style = MATCH_BADGE[result.match_label];
                  return (
                    <div
                      className="p-4 space-y-3"
                      style={{ background: "#fafafa", border: "1px solid #e8e8e8" }}
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className="text-[10px] tracking-[0.2em] text-[#888]"
                          style={SANS}
                        >
                          MATCH RESULT
                        </span>
                        <span
                          className={`text-[10px] tracking-[0.1em] px-3 py-1 ${style.bg} ${style.text}`}
                          style={SANS}
                        >
                          {result.match_label.toUpperCase()}
                        </span>
                      </div>

                      {/* Semicircular gauge: background arc (grey) + filled arc (coloured by match
                          quality) + rotating needle, all derived from result.delta_e and gaugeAngle */}
                      <div className="flex items-center justify-center py-1">
                        <svg width="180" height="100" viewBox="0 0 180 100">
                          <path
                            d="M10 95 A80 80 0 0 1 170 95"
                            fill="none"
                            stroke="#e8e8e8"
                            strokeWidth="10"
                            strokeLinecap="round"
                          />
                          <path
                            d="M10 95 A80 80 0 0 1 170 95"
                            fill="none"
                            stroke={style.bar}
                            strokeWidth="10"
                            strokeLinecap="round"
                            strokeDasharray={`${Math.min(100, Math.max(0, result.delta_e)) * 2.51} 251`}
                          />
                          <line
                            x1="90"
                            y1="95"
                            x2="90"
                            y2="28"
                            stroke="#111"
                            strokeWidth="2"
                            strokeLinecap="round"
                            transform={`rotate(${gaugeAngle} 90 95)`}
                          />
                          <circle cx="90" cy="95" r="4.5" fill="#111" />
                        </svg>
                      </div>

                      <p className="text-xs text-center" style={{ ...SANS, fontWeight: 300, color: "#888" }}>
                        Matching score:{" "}
                        <span className="font-medium" style={{ color: "#111" }}>
                          {result.delta_e}
                        </span>
                        &nbsp;— {style.desc}
                      </p>
                    </div>
                  );
                })()}

                {/* CVD distinguishability block — shows per-garment feedback on whether
                    the colour is distinguishable under the user's selected vision type */}
                <div
                  className="p-4 space-y-2"
                  style={{ background: "#fafafa", border: "1px solid #e8e8e8" }}
                >
                  <p
                    className="text-[10px] tracking-[0.2em] text-[#888]"
                    style={SANS}
                  >
                    VISIBILITY UNDER YOUR VISION TYPE
                  </p>
                  {result.cvd_type === "Normal" ? (
                    <DistRow
                      ok
                      text="Both colours are fully distinguishable with normal vision."
                    />
                  ) : (
                    <>
                      <DistRow
                        ok={!result.top_hard}
                        text={
                          result.top_hard
                            ? `Top — hard to distinguish under ${result.cvd_type}.`
                            : `Top  — distinguishable under ${result.cvd_type}.`
                        }
                      />
                      <DistRow
                        ok={!result.bottom_hard}
                        text={
                          result.bottom_hard
                            ? `Bottom — hard to distinguish under ${result.cvd_type}.`
                            : `Bottom — distinguishable under ${result.cvd_type}.`
                        }
                      />
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * DistRow
 * Small presentational row used in the "Visibility under your vision type"
 * section. Renders a coloured status dot (green = ok, amber = hard to
 * distinguish) next to a line of explanatory text.
 */
function DistRow({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div className="flex items-start gap-2.5 py-1">
      <div
        className="mt-0.5 w-2.5 h-2.5 rounded-full flex-shrink-0"
        style={{ background: ok ? "#3F7A4A" : "#D6A32E" }}
      />
      <p className="text-sm" style={{ color: "#555" }}>
        {text}
      </p>
    </div>
  );
}