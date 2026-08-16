"use client";

import { ImagePlus } from "lucide-react";
import { useState, type ChangeEvent, type FormEvent } from "react";
import { SANS, SERIF } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/";
const API_URL = `${API_BASE.replace(/\/$/, "")}/coloranalyzer`;

interface CvdResult {
  success: boolean;
  cvd_type: string;
  cvd_image: string;
  detail?: string;
}

const CVD_LABELS: Record<string, string> = {
  protanopia: "Protanopia — red-blind",
  deuteranopia: "Deuteranopia — green-blind",
  tritanopia: "Tritanopia — blue-blind",
};

export function CvdTab() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [cvdType, setCvdType] = useState("protanopia");
  const [result, setResult] = useState<CvdResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select an image first");
      return;
    }

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("cvd_type", cvdType);

      const res = await fetch(`${API_URL}/generate-cvd`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!data.success) throw new Error(data.detail || "CVD generation failed");
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* CONTROLS BAR */}
      <div className="flex flex-wrap items-end gap-5 border-b border-[#e8e8e8] p-6 md:p-8">
        <div className="min-w-[240px] flex-1">
          <p className="mb-2 text-[10px] tracking-[0.25em] text-[#aaa]" style={SANS}>
            PHOTO
          </p>
          <label className="flex cursor-pointer items-center gap-3 border border-dashed border-[#d7d7d7] px-4 py-3 transition hover:border-[#111] hover:bg-[#f5f5f5]">
            <ImagePlus className="h-4 w-4 flex-shrink-0 text-[#777]" />
            <span
              className="truncate text-sm text-[#111]"
              style={{ ...SANS, fontWeight: 400 }}
            >
              {file ? file.name : "Select a photo to simulate"}
            </span>
            <input
              type="file"
              accept="image/*"
              onChange={handleFile}
              className="hidden"
            />
          </label>
        </div>

        <div className="min-w-[220px]">
          <p className="mb-2 text-[10px] tracking-[0.25em] text-[#aaa]" style={SANS}>
            CVD TYPE
          </p>
          <select
            value={cvdType}
            onChange={(e) => setCvdType(e.target.value)}
            className="w-full border border-[#d7d7d7] bg-white px-3 py-2.5 text-sm text-[#111] outline-none focus:border-[#111]"
            style={SANS}
          >
            {Object.entries(CVD_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <Button
          type="submit"
          disabled={loading || !file}
          className="rounded-none border border-[#111] bg-[#111] px-8 py-2.5 text-[11px] tracking-[0.2em] text-white transition-all hover:bg-[#222] disabled:border-[#ddd] disabled:bg-[#ddd] disabled:text-[#999]"
          style={SANS}
        >
          {loading ? "SIMULATING…" : "SIMULATE CVD"}
        </Button>
      </div>

      {error && (
        <p
          className="mx-6 mt-6 border border-[#f1cfc7] bg-[#fbeae6] px-4 py-3 text-xs leading-6 text-[#9a3b2e] md:mx-8"
          style={SANS}
        >
          {error}
        </p>
      )}

      {/* PREVIEW / RESULTS */}
      <div className="bg-[#fafafa] p-6 md:p-8">
        {!result ? (
          preview ? (
            <div className="mx-auto max-w-2xl border border-[#e8e8e8] bg-white p-4">
              <img
                src={preview}
                alt="Preview"
                className="mx-auto max-h-[560px] w-full object-contain"
              />
            </div>
          ) : (
            <div
              className="flex min-h-80 flex-col items-center justify-center gap-3 text-center text-[#999]"
              style={SANS}
            >
              <div className="h-1.5 w-1.5 bg-[#111]" />
              <p className="text-sm">
                Simulated vision will appear here once you run it.
              </p>
            </div>
          )
        ) : (
          <div>
            <h2
              className="mb-6 text-xl capitalize tracking-[0.15em] text-[#111]"
              style={{ ...SERIF, fontWeight: 500 }}
            >
              {result.cvd_type}
            </h2>
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <p className="mb-3 text-[10px] tracking-[0.2em] text-[#aaa]" style={SANS}>
                  ORIGINAL
                </p>
                <div className="flex min-h-[420px] items-center justify-center border border-[#e8e8e8] bg-white p-4">
                  {preview && (
                    <img
                      src={preview}
                      alt="Original"
                      className="max-h-[560px] w-full object-contain"
                    />
                  )}
                </div>
              </div>
              <div>
                <p className="mb-3 text-[10px] tracking-[0.2em] text-[#aaa]" style={SANS}>
                  SIMULATED
                </p>
                <div className="flex min-h-[420px] items-center justify-center border border-[#e8e8e8] bg-white p-4">
                  <img
                    src={`data:image/jpeg;base64,${result.cvd_image}`}
                    alt="CVD simulation"
                    className="max-h-[560px] w-full object-contain"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </form>
  );
}