"use client";

import { useState, useRef } from "react";

type ColorInfo = {
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
  Protanopia: "Protanopia — red-blind",
  Deuteranopia: "Deuteranopia — green-blind",
  Tritanopia: "Tritanopia — blue-blind",
};

const MATCH_BADGE: Record<
  string,
  { bg: string; text: string; bar: string; desc: string }
> = {
  "Good match": {
    bg: "bg-green-100",
    text: "text-green-800",
    bar: "#639922",
    desc: "These colours pair well together — good contrast.",
  },
  "Moderate match": {
    bg: "bg-yellow-100",
    text: "text-yellow-800",
    bar: "#BA7517",
    desc: "Acceptable pairing — some contrast but not ideal.",
  },
  "Poor match": {
    bg: "bg-red-100",
    text: "text-red-800",
    bar: "#A32D2D",
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

  return (
    <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-100 p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900">
          CVD Clothing Matcher
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Upload your top and bottom clothing to check how well they match.
        </p>
      </div>

      {/* CVD selector */}
      <div className="space-y-1.5">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Your vision type
        </label>
        <select
          value={cvdType}
          onChange={(e) => {
            setCvdType(e.target.value);
            setResult(null);
          }}
          className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm text-gray-800 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-200"
        >
          {CVD_OPTIONS.map((o) => (
            <option key={o} value={o}>
              {CVD_DESCRIPTIONS[o]}
            </option>
          ))}
        </select>
      </div>

      {/* Upload row */}
      <div className="space-y-1.5">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Upload clothing images
        </label>
        <div className="grid grid-cols-2 gap-3">
          {(["top", "bottom"] as const).map((which) => {
            const preview = which === "top" ? topPreview : botPreview;
            const inputRef = which === "top" ? topRef : botRef;
            const emoji = which === "top" ? "👕" : "👖";
            const label = which === "top" ? "Top" : "Bottom";
            return (
              <div key={which} className="flex flex-col gap-1">
                <span className="text-xs text-gray-400 text-center">
                  {label}
                </span>
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="w-full h-36 rounded-xl border-2 border-dashed border-gray-200 hover:border-gray-400 bg-gray-50 hover:bg-gray-100 transition flex flex-col items-center justify-center gap-2 overflow-hidden relative"
                >
                  {preview ? (
                    <img
                      src={preview}
                      alt={label}
                      className="absolute inset-0 w-full h-full object-cover rounded-xl"
                    />
                  ) : (
                    <>
                      <span style={{ fontSize: 28 }}>{emoji}</span>
                      <span className="text-xs text-gray-400">
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
        className="w-full py-3 rounded-xl border border-gray-200 text-sm font-semibold text-gray-700 hover:bg-gray-50 active:scale-95 transition disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-4 w-4 text-gray-500"
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
        <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4 border-t border-gray-100 pt-5">
          {/* Colour swatches */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Dominant colours detected
            </p>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Top", color: result.top_color },
                { label: "Bottom", color: result.bottom_color },
              ].map(({ label, color }) => (
                <div
                  key={label}
                  className="flex flex-col items-center gap-2 bg-gray-50 rounded-xl p-3 border border-gray-100"
                >
                  <span className="text-xs text-gray-400 uppercase tracking-wide">
                    {label}
                  </span>
                  <div
                    className="w-14 h-14 rounded-full border-2 border-white shadow-sm"
                    style={{ background: color.hex }}
                  />
                  <span className="text-sm font-semibold text-gray-800">
                    {color.name}
                  </span>
                  <span className="text-xs text-gray-400 font-mono">
                    {color.hex.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Match result */}
          {(() => {
            const style = MATCH_BADGE[result.match_label];
            const barPct = Math.min(100, Math.max(4, result.delta_e));
            return (
              <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-700">
                    Match result
                  </span>
                  <span
                    className={`text-xs font-semibold px-3 py-1 rounded-full ${style.bg} ${style.text}`}
                  >
                    {result.match_label}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-2 rounded-full transition-all duration-700"
                    style={{ width: `${barPct}%`, background: style.bar }}
                  />
                </div>
                <p className="text-xs text-gray-400">
                  Delta E score:{" "}
                  <span className="font-mono font-semibold text-gray-600">
                    {result.delta_e}
                  </span>
                  &nbsp;— {style.desc}
                </p>
              </div>
            );
          })()}

          {/* CVD distinguishability */}
          <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 space-y-2">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
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
      )}
    </div>
  );
}

function DistRow({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div className="flex items-start gap-2.5 py-1">
      <div
        className={`mt-0.5 w-3 h-3 rounded-full flex-shrink-0 ${ok ? "bg-green-500" : "bg-yellow-400"}`}
      />
      <p className="text-sm text-gray-700">{text}</p>
    </div>
  );
}
