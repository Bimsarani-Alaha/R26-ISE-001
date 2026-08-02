"use client";

import { useState } from "react";
import Link from "next/link";

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [resultImage, setResultImage] = useState<string>("");
  const [measurements, setMeasurements] = useState<any[]>([]);
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
        setMessage(
          "Prediction completed but no measurement data was returned.",
        );
      }
    } catch (err) {
      console.error(err);
      setMessage(
        "Error connecting to server. Make sure the backend is running.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 sm:px-6 lg:px-8">
      <section className="mx-auto flex max-w-6xl flex-col gap-6">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl shadow-black/20 backdrop-blur">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-2xl">
              <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Pose Detection Demo
              </h1>
              <p className="mt-3 text-sm text-slate-300 sm:text-base">
                Upload an image, enter your height, and predict pose
                measurements.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link href="/about">
                <button className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-100 transition hover:bg-slate-700">
                  About
                </button>
              </Link>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/60 px-4 py-8 text-center transition hover:border-sky-400 hover:bg-slate-800/80">
                <span className="text-sm font-medium text-slate-200">
                  Select Image
                </span>
                <span className="mt-2 text-xs text-slate-400">
                  PNG, JPG, WEBP, and more
                </span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleChange}
                  className="hidden"
                />
              </label>

              {file && (
                <div className="text-sm text-slate-400">{file.name}</div>
              )}

              <div className="space-y-2">
                <label
                  htmlFor="height"
                  className="text-sm font-medium text-slate-200"
                >
                  Height (cm)
                </label>
                <input
                  id="height"
                  type="number"
                  min="1"
                  step="0.1"
                  placeholder="e.g. 172.5"
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none ring-0 focus:border-sky-500"
                />
              </div>

              <button
                className="w-full rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={handleUpload}
                disabled={loading}
              >
                {loading ? "Processing..." : "Predict Image"}
              </button>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-sm text-slate-300">
              <h2 className="text-base font-semibold text-white">
                How it works
              </h2>
              <ul className="mt-3 space-y-2 leading-6">
                <li>• Upload a full-body image.</li>
                <li>• Enter your real height for better scaling.</li>
                <li>• Review the annotated image and measurements.</li>
              </ul>
            </div>
          </div>

          {message && (
            <div className="mt-4 rounded-xl border border-sky-700/40 bg-sky-950/30 px-4 py-3 text-sm text-sky-200">
              {message}
            </div>
          )}
        </div>

        <section className="space-y-4">
          {(preview || resultImage) && (
            <div className="grid gap-4 lg:grid-cols-2">
              {preview && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                  <h3 className="mb-3 text-lg font-semibold text-white">
                    Original
                  </h3>
                  <img
                    src={preview}
                    alt="Original upload preview"
                    className="h-auto w-full rounded-xl object-contain"
                  />
                </div>
              )}

              {resultImage && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
                  <h3 className="mb-3 text-lg font-semibold text-white">
                    Result
                  </h3>
                  <img
                    src={resultImage}
                    alt="Annotated result"
                    className="h-auto w-full rounded-xl object-contain"
                  />
                </div>
              )}
            </div>
          )}

          {measurements.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
              <h3 className="mb-4 text-lg font-semibold text-white">
                Measurements
              </h3>

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {measurements.map((m, i) => (
                  <div
                    className="rounded-xl border border-slate-800 bg-slate-950/70 p-3"
                    key={i}
                  >
                    <div className="text-sm text-slate-400">Shoulder (px)</div>
                    <div className="text-base font-semibold text-white">
                      {m.shoulder_width?.toFixed(1) ?? "N/A"}
                    </div>

                    <div className="mt-2 text-sm text-slate-400">Hip (px)</div>
                    <div className="text-base font-semibold text-white">
                      {m.hip_width?.toFixed(1) ?? "N/A"}
                    </div>

                    <div className="mt-2 text-sm text-slate-400">
                      Height (px)
                    </div>
                    <div className="text-base font-semibold text-white">
                      {m.height?.toFixed(1) ?? "N/A"}
                    </div>

                    <div className="mt-2 text-sm text-slate-400">
                      Shoulder (cm)
                    </div>
                    <div className="text-base font-semibold text-white">
                      {m.shoulder_cm?.toFixed(2) ?? "N/A"}
                    </div>

                    <div className="mt-2 text-sm text-slate-400">Hip (cm)</div>
                    <div className="text-base font-semibold text-white">
                      {m.hip_cm?.toFixed(2) ?? "N/A"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
