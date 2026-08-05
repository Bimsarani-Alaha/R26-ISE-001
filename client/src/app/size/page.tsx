"use client";

import { ArrowUpRight, ImagePlus, Sparkles } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useState, type ChangeEvent } from "react";
import { SANS, SERIF, StyleAiWordmark } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";

type Measurement = {
  shoulder_width?: number;
  hip_width?: number;
  height?: number;
  shoulder_cm?: number;
  hip_cm?: number;
};

export default function SizePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [resultImage, setResultImage] = useState<string>("");
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [height, setHeight] = useState("");

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
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
        setMessage("Prediction completed but no measurement data was returned.");
      }
    } catch (err) {
      console.error(err);
      setMessage("Error connecting to server. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-white text-[#111]">
      <nav className="flex items-center justify-between border-b border-[#e8e8e8] px-8 py-6 md:px-16">
        <div className="flex items-center gap-8">
          {[
            { label: "HOME", href: "/" },
            { label: "INPUT", href: "/input" },
            { label: "POSE", href: "/size" },
          ].map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => router.push(item.href)}
              className="hidden text-xs tracking-[0.15em] text-[#111] transition-colors hover:text-[#888] md:block"
              style={{ ...SANS, fontWeight: 400 }}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="text-center">
          <StyleAiWordmark className="text-2xl" />
        </div>

        <div className="flex items-center gap-6">
          <Button
            onClick={() => router.push("/input")}
            variant="ghost"
            size="sm"
            className="hidden h-auto rounded-none bg-transparent p-0 text-xs tracking-[0.15em] text-[#111] hover:bg-transparent hover:text-[#888] md:block"
            style={{ ...SANS, fontWeight: 400 }}
          >
            LOGIN
          </Button>
          <Button
            onClick={() => router.push("/size")}
            variant="outline"
            size="sm"
            className="h-auto rounded-none border-[#111] px-4 py-1.5 text-xs tracking-[0.15em] text-[#111] transition-colors hover:bg-[#111] hover:text-white"
            style={{ ...SANS, fontWeight: 400 }}
          >
            POSE DETECTION
          </Button>
        </div>
      </nav>

      <main className="px-8 py-10 md:px-16 md:py-16">
        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="overflow-hidden rounded-none border border-[#e8e8e8] bg-[#f7f4ee] shadow-[0_20px_80px_-30px_rgba(17,17,17,0.25)]"
        >
          <div className="grid lg:grid-cols-[1.1fr_0.9fr]">
            <div className="relative min-h-[420px] overflow-hidden rounded-none">
              <img
                src="/sizeHome.jpg"
                alt="Size measurement hero image"
                className="absolute inset-0 h-full w-full rounded-none object-cover object-top"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/20 to-transparent" />

              <div className="relative flex h-full flex-col justify-between p-8 sm:p-10 lg:p-12">

                <div className="max-w-xl">
                  <h1
                    className="text-4xl text-white sm:text-5xl lg:text-6xl"
                    style={{ ...SERIF, fontWeight: 300 }}
                  >
                    POSE DETECTION
                  </h1>
                  <p className="mt-4 max-w-lg text-sm leading-7 text-white/80 sm:text-base" style={SANS}>
                    Upload a full-body image, enter your real height, and receive refined measurements with the same calm, editorial experience as the rest of the platform.
                  </p>
                  <div className="mt-8 flex flex-wrap gap-3">
                    <Button
                      onClick={() => router.push("/input")}
                      className="flex items-center gap-2 rounded-none border border-white bg-white px-6 py-3 text-[11px] tracking-[0.2em] text-[#111] transition-all hover:bg-[#f2f2f2]"
                      style={{ ...SANS, fontWeight: 400 }}
                    >
                      START NOW
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      onClick={() => router.push("/")}
                      variant="ghost"
                      className="flex items-center gap-2 rounded-none border border-white/70 bg-transparent px-6 py-3 text-[11px] tracking-[0.2em] text-white transition-all hover:bg-white hover:text-[#111]"
                      style={{ ...SANS, fontWeight: 400 }}
                    >
                      BACK HOME
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-col justify-center bg-white p-8 sm:p-10 lg:p-12">
              <div className="mb-4 flex items-center gap-2 text-[11px] tracking-[0.25em] text-[#777]" style={SANS}>
                START YOUR ANALYSIS
              </div>

              <div className="border border-[#e5e5e5] bg-[#fafafa] p-6 sm:p-7">
                <label className="flex cursor-pointer flex-col items-center justify-center border border-dashed border-[#d7d7d7] bg-white px-4 py-8 text-center transition hover:border-[#111] hover:bg-[#f5f5f5]">
                  <ImagePlus className="h-6 w-6 text-[#777]" />
                  <span className="mt-3 text-sm font-medium text-[#111]">
                    Select Image
                  </span>
                  <span className="mt-2 text-xs text-[#777]">
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
                  <div className="mt-3 text-xs uppercase tracking-[0.2em] text-[#666]">
                    {file.name}
                  </div>
                )}

                <div className="mt-5 space-y-2">
                  <label htmlFor="height" className="text-sm font-medium text-[#111]">
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
                    className="w-full rounded-none border border-[#d7d7d7] bg-white px-3 py-2.5 text-sm text-[#111] outline-none ring-0 focus:border-[#111]"
                  />
                </div>

                <Button
                  className="mt-5 w-full rounded-none border border-[#111] bg-[#111] px-4 py-3 text-[11px] tracking-[0.2em] text-white transition-all hover:bg-[#222]"
                  onClick={handleUpload}
                  disabled={loading}
                  style={{ ...SANS, fontWeight: 400 }}
                >
                  {loading ? "PROCESSING..." : "PREDICT IMAGE"}
                </Button>

                {message && (
                  <p className="mt-4 text-sm leading-6 text-[#666]">{message}</p>
                )}
              </div>
            </div>
          </div>
        </motion.section>

        <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.4 }}
              className="border border-[#e8e8e8] bg-white p-8"
            >
              <h3 className="text-xl tracking-[0.2em] text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>
                MEASUREMENTS
              </h3>

              {measurements.length > 0 ? (
                <div className="mt-6 space-y-4">
                  {measurements.map((m, i) => (
                    <div key={`${m.shoulder_width ?? "n"}-${i}`} className="grid gap-4 border border-[#e5e5e5] bg-[#fafafa] p-5 md:grid-cols-[0.95fr_0.95fr]">
                      <div>
                        <div className="text-[10px] uppercase tracking-[0.25em] text-[#999]" style={SANS}>
                          PIXELS
                        </div>
                        <div className="mt-4 text-sm text-[#777]" style={SANS}>Shoulder</div>
                        <div className="text-base font-semibold text-[#111]">
                          {m.shoulder_width?.toFixed(1) ?? "N/A"}
                        </div>
                        <div className="mt-3 text-sm text-[#777]" style={SANS}>Hip</div>
                        <div className="text-base font-semibold text-[#111]">
                          {m.hip_width?.toFixed(1) ?? "N/A"}
                        </div>
                        <div className="mt-3 text-sm text-[#777]" style={SANS}>Height</div>
                        <div className="text-base font-semibold text-[#111]">
                          {m.height?.toFixed(1) ?? "N/A"}
                        </div>
                      </div>

                      <div>
                        <div className="text-[10px] uppercase tracking-[0.25em] text-[#999]" style={SANS}>
                          CENTIMETERS
                        </div>
                        <div className="mt-4 text-sm text-[#777]" style={SANS}>Shoulder</div>
                        <div className="text-base font-semibold text-[#111]">
                          {m.shoulder_cm?.toFixed(2) ?? "N/A"}
                        </div>
                        <div className="mt-3 text-sm text-[#777]" style={SANS}>Hip</div>
                        <div className="text-base font-semibold text-[#111]">
                          {m.hip_cm?.toFixed(2) ?? "N/A"}
                        </div>
                        <div className="mt-3 text-sm text-[#777]" style={SANS}>Height</div>
                        <div className="text-base font-semibold text-[#111]">
                          {m.height ? "--" : "N/A"}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-6 border border-dashed border-[#d7d7d7] bg-[#fafafa] p-6 text-sm leading-7 text-[#666]" style={SANS}>
                  Upload an image and run the predictor to reveal the measurements panel here.
                </div>
              )}
            </motion.div>

        <section className="mt-10 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="border border-[#e8e8e8] bg-[#fafafa] p-8"
          >
            <h2 className="text-2xl tracking-[0.2em] text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>
              HOW IT WORKS
            </h2>
            <div className="mt-6 space-y-4">
              {[
                {
                  title: "01 · UPLOAD",
                  desc: "Upload a clear full-body image. For more accurate size prediction, stand approximately 2 meters away from the camera while capturing the image",
                },
                {
                  title: "02 · SCALE",
                  desc: "Enter your real height in centimeters (cm). The system uses your height to accurately convert the detected shoulder and hip measurements into centimeters.",
                },
                {
                  title: "03 · REVIEW",
                  desc: "Review the processed image and the calculated body measurements, including your shoulder width, hip width, and height.",
                },
                {
                  title: "04 · SIZE",
                  desc: "Based on your body measurements, the system recommends the most suitable torso clothing size (S, M, L, XL, etc.) for a better fit.",
                },
              ].map((item) => (
                <div key={item.title} className="border-b border-[#e5e5e5] pb-4 last:border-b-0 last:pb-0">
                  <p className="text-[11px] tracking-[0.25em] text-[#aaa]" style={SANS}>
                    {item.title}
                  </p>
                  <p className="mt-2 text-sm leading-7 text-[#666]" style={SANS}>
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>

          

          <div className="space-y-6">
            {(preview || resultImage) && (
              <div className="grid gap-6 md:grid-cols-2">
                {preview && (
                  <motion.div
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="border border-[#e8e8e8] bg-white p-5"
                  >
                    <h3 className="text-lg tracking-[0.15em] text-[#111]" style={{ ...SERIF, fontWeight: 500 }}>
                      ORIGINAL
                    </h3>
                    <img
                      src={preview}
                      alt="Original upload preview"
                      className="mt-4 h-auto w-full object-contain"
                    />
                  </motion.div>
                )}

                {resultImage && (
                  <motion.div
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                    className="border border-[#e8e8e8] bg-white p-5"
                  >
                    <h3 className="text-lg tracking-[0.15em] text-[#111]" style={{ ...SERIF, fontWeight: 500 }}>
                      RESULT
                    </h3>
                    <img
                      src={resultImage}
                      alt="Annotated result"
                      className="mt-4 h-auto w-full object-contain"
                    />
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
