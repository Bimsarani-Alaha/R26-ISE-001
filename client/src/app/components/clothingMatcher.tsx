"use client";

import { useState, useRef } from "react";

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
    bg: "bg-[#E7F3EF]",
    text: "text-[#2B6E5E]",
    bar: "#2B6E5E",
    desc: "These colours pair well together — good contrast.",
  },
  "Moderate match": {
    bg: "bg-[#FBF1DE]",
    text: "text-[#9C6B1A]",
    bar: "#B4791E",
    desc: "Acceptable pairing — some contrast but not ideal.",
  },
  "Poor match": {
    bg: "bg-[#FBE9E7]",
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
      const res = await fetch("http://localhost:8000/analyse", {
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

  const canAnalyse = !!topFile && !!botFile && !loading;

  // Presentational only — derives gauge needle angle from the existing
  // result.delta_e value. No new state, no new logic.
  const gaugeAngle = result
    ? -90 + Math.min(100, Math.max(0, result.delta_e)) * 1.8
    : -90;

  return (
    <>
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
      />
      <div
        className="w-full max-w-md rounded-2xl border overflow-hidden"
        style={{
          background: "#FFFFFF",
          borderColor: "#E1E4EA",
          boxShadow: "0 1px 2px rgba(16,20,28,0.04), 0 12px 32px -12px rgba(16,20,28,0.12)",
          fontFamily: "'Inter', sans-serif",
        }}
      >
        {/* Spectral calibration strip — signature element */}
        <div
          className="h-1.5 w-full"
          style={{
            background:
              "linear-gradient(90deg, #B0453F 0%, #B4791E 18%, #D6C24A 36%, #3F7A4A 54%, #2B6E6E 72%, #3A5FA0 88%, #6B4C9A 100%)",
          }}
        />

        <div className="p-8 space-y-7">
          {/* Header */}
          <div className="space-y-1.5">
            <span
              className="text-[10px] font-medium uppercase tracking-[0.14em]"
              style={{ color: "#2B6E6E", fontFamily: "'IBM Plex Mono', monospace" }}
            >
              Colour Vision Tool
            </span>
            <h1
              className="text-[22px] leading-tight font-semibold"
              style={{ color: "#12151A", fontFamily: "'Space Grotesk', sans-serif" }}
            >
              CVD Clothing Matcher
            </h1>
            <p className="text-sm" style={{ color: "#667085" }}>
              Upload your top and bottom clothing to check how well they match.
            </p>
          </div>

          {/* CVD selector */}
          <div className="space-y-1.5">
            <label
              className="text-[11px] font-medium uppercase tracking-wide"
              style={{ color: "#667085", fontFamily: "'IBM Plex Mono', monospace" }}
            >
              Your vision type
            </label>
            <div className="relative">
              <select
                value={cvdType}
                onChange={(e) => {
                  setCvdType(e.target.value);
                  setResult(null);
                }}
                className="w-full appearance-none rounded-xl px-3.5 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 transition"
                style={{
                  color: "#12151A",
                  background: "#F5F6F8",
                  border: "1px solid #E1E4EA",
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
                  stroke="#8A93A3"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>

          {/* Upload row */}
          <div className="space-y-1.5">
            <label
              className="text-[11px] font-medium uppercase tracking-wide"
              style={{ color: "#667085", fontFamily: "'IBM Plex Mono', monospace" }}
            >
              Upload clothing images
            </label>
            <div className="grid grid-cols-2 gap-3">
              {(["top", "bottom"] as const).map((which) => {
                const preview = which === "top" ? topPreview : botPreview;
                const inputRef = which === "top" ? topRef : botRef;
                const label = which === "top" ? "Top" : "Bottom";
                return (
                  <div key={which} className="flex flex-col gap-1.5">
                    <span
                      className="text-[11px] text-center font-medium"
                      style={{ color: "#8A93A3" }}
                    >
                      {label}
                    </span>
                    <button
                      type="button"
                      onClick={() => inputRef.current?.click()}
                      className="w-full h-36 rounded-xl transition flex flex-col items-center justify-center gap-2 overflow-hidden relative group"
                      style={{
                        border: preview ? "1px solid #E1E4EA" : "1.5px dashed #C9CEDA",
                        background: preview ? "transparent" : "#F5F6F8",
                      }}
                    >
                      {preview ? (
                        <img
                          src={preview}
                          alt={label}
                          className="absolute inset-0 w-full h-full object-cover rounded-xl"
                        />
                      ) : (
                        <>
                          <svg
                            width="26"
                            height="26"
                            viewBox="0 0 24 24"
                            fill="none"
                            className="transition group-hover:opacity-80"
                          >
                            <path
                              d="M9 3L7 5H4a1 1 0 00-1 1v13a1 1 0 001 1h16a1 1 0 001-1V6a1 1 0 00-1-1h-3l-2-2H9z"
                              stroke="#9AA2B1"
                              strokeWidth="1.4"
                              strokeLinejoin="round"
                            />
                            <circle cx="12" cy="13" r="3.4" stroke="#9AA2B1" strokeWidth="1.4" />
                          </svg>
                          <span className="text-[11px]" style={{ color: "#9AA2B1" }}>
                            Click to upload
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

          {/* Analyse button */}
          <button
            type="button"
            onClick={analyse}
            disabled={!canAnalyse}
            className="w-full py-3 rounded-xl text-sm font-semibold transition active:scale-[0.98] disabled:cursor-not-allowed"
            style={{
              background: canAnalyse ? "#1F6F6B" : "#E1E4EA",
              color: canAnalyse ? "#FFFFFF" : "#9AA2B1",
              fontFamily: "'Space Grotesk', sans-serif",
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
                Analysing…
              </span>
            ) : (
              "Analyse colours →"
            )}
          </button>

          {/* Error */}
          {error && (
            <div
              className="rounded-xl px-4 py-3 text-sm"
              style={{ background: "#FBE9E7", border: "1px solid #F3CFCB", color: "#A3372E" }}
            >
              {error}
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-5 pt-1" style={{ borderTop: "1px solid #EDEFF3" }}>
              <div className="pt-5 space-y-5">
                {/* Colour swatches */}
                <div>
                  <p
                    className="text-[11px] font-medium uppercase tracking-wide mb-2"
                    style={{ color: "#667085", fontFamily: "'IBM Plex Mono', monospace" }}
                  >
                    Dominant colours detected
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: "Top", color: result.top_color },
                      { label: "Bottom", color: result.bottom_color },
                    ].map(({ label, color }) => (
                      <div
                        key={label}
                        className="flex flex-col items-center gap-2 rounded-xl p-3.5"
                        style={{ background: "#F5F6F8", border: "1px solid #E1E4EA" }}
                      >
                        <span
                          className="text-[10px] uppercase tracking-wide"
                          style={{ color: "#9AA2B1" }}
                        >
                          {label}
                        </span>

                        <div
                          className="w-14 h-14 rounded-full"
                          style={{
                            background: color.hex,
                            border: "3px solid #FFFFFF",
                            boxShadow: "0 0 0 1px #E1E4EA",
                          }}
                        />
                        <span
                          className="text-sm font-semibold"
                          style={{ color: "#12151A", fontFamily: "'Space Grotesk', sans-serif" }}
                        >
                          {color.name}
                        </span>
                        <span
                          className="text-[10px]"
                          style={{ color: "#9AA2B1", fontFamily: "'IBM Plex Mono', monospace" }}
                        >
                          {color.hex.toUpperCase()}
                        </span>

                        {color.palette && color.palette.length > 1 && (
                          <div className="flex gap-1 mt-1">
                            {color.palette.map(
                              (p: { hex: string; percentage: number }, i: number) => (
                                <div
                                  key={i}
                                  className="flex flex-col items-center gap-0.5"
                                >
                                  <div
                                    className="w-6 h-6 rounded"
                                    style={{ background: p.hex, border: "1px solid #FFFFFF", boxShadow: "0 0 0 1px #E1E4EA" }}
                                  />
                                  <span
                                    className="text-[9px]"
                                    style={{ color: "#9AA2B1", fontFamily: "'IBM Plex Mono', monospace" }}
                                  >
                                    {p.percentage}%
                                  </span>
                                </div>
                              ),
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Match result — Delta E gauge */}
                {(() => {
                  const style = MATCH_BADGE[result.match_label];
                  return (
                    <div
                      className="rounded-xl p-4 space-y-3"
                      style={{ background: "#F5F6F8", border: "1px solid #E1E4EA" }}
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className="text-[11px] font-medium uppercase tracking-wide"
                          style={{ color: "#667085", fontFamily: "'IBM Plex Mono', monospace" }}
                        >
                          Match result
                        </span>
                        <span
                          className={`text-xs font-semibold px-3 py-1 rounded-full ${style.bg} ${style.text}`}
                        >
                          {result.match_label}
                        </span>
                      </div>

                      {/* Semicircular gauge, driven entirely by result.delta_e */}
                      <div className="flex items-center justify-center py-1">
                        <svg width="180" height="100" viewBox="0 0 180 100">
                          <path
                            d="M10 95 A80 80 0 0 1 170 95"
                            fill="none"
                            stroke="#E1E4EA"
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
                            stroke="#12151A"
                            strokeWidth="2"
                            strokeLinecap="round"
                            transform={`rotate(${gaugeAngle} 90 95)`}
                          />
                          <circle cx="90" cy="95" r="4.5" fill="#12151A" />
                        </svg>
                      </div>

                      <p className="text-xs text-center" style={{ color: "#8A93A3" }}>
                        Delta E score:{" "}
                        <span
                          className="font-semibold"
                          style={{ color: "#12151A", fontFamily: "'IBM Plex Mono', monospace" }}
                        >
                          {result.delta_e}
                        </span>
                        &nbsp;— {style.desc}
                      </p>
                    </div>
                  );
                })()}

                {/* CVD distinguishability */}
                <div
                  className="rounded-xl p-4 space-y-2"
                  style={{ background: "#F5F6F8", border: "1px solid #E1E4EA" }}
                >
                  <p
                    className="text-[11px] font-medium uppercase tracking-wide"
                    style={{ color: "#667085", fontFamily: "'IBM Plex Mono', monospace" }}
                  >
                    Visibility under your vision type
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
                            ? `Top (${result.top_color.name}) — hard to distinguish under ${result.cvd_type}.`
                            : `Top (${result.top_color.name}) — distinguishable under ${result.cvd_type}.`
                        }
                      />
                      <DistRow
                        ok={!result.bottom_hard}
                        text={
                          result.bottom_hard
                            ? `Bottom (${result.bottom_color.name}) — hard to distinguish under ${result.cvd_type}.`
                            : `Bottom (${result.bottom_color.name}) — distinguishable under ${result.cvd_type}.`
                        }
                      />
                    </>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function DistRow({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div className="flex items-start gap-2.5 py-1">
      <div
        className="mt-0.5 w-3 h-3 rounded-full flex-shrink-0"
        style={{ background: ok ? "#3F7A4A" : "#D6A32E" }}
      />
      <p className="text-sm" style={{ color: "#3D4451" }}>
        {text}
      </p>
    </div>
  );
}