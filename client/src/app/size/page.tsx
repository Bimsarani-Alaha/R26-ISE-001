"use client";

import { ArrowUpRight, Camera, Focus, ImagePlus } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { SANS, SERIF, StyleAiWordmark } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";
import { useAppStore } from "@/app/context/AppStoreContext";

type Measurement = {
  shoulder_width?: number;
  hip_width?: number;
  height?: number;
  height_cm?: number;
  height_m?: number;
  height_is_estimated?: boolean;
  shoulder_cm?: number;
  hip_cm?: number;
  size?: string;
};

type PredictionMode = "camera" | "upload";

type PoseReadiness = {
  ready: boolean;
  message: string;
  reason: string | null;
  box: [number, number, number, number] | null;
  frame_width: number;
  frame_height: number;
};

const POSE_CHECK_INTERVAL_MS = 1000;
const POSE_REQUEST_TIMEOUT_MS = 15000;
const MAX_CAPTURE_DIMENSION = 1280;
const CAPTURE_JPEG_QUALITY = 0.85;
type ApiMode = "PC" | "MOBILE";
const MODE: ApiMode = "MOBILE";
const getApiBaseUrl = (mode: ApiMode = MODE) => {
  const mobileApiUrl =
    process.env.NEXT_PUBLIC_MOBILE_URL?.replace(/\/+$/, "") ||
    "https://mds3m8h8-8000.asse.devtunnels.ms";
  const pcApiUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ||
    "http://localhost:8000";
  return mode === "MOBILE" ? mobileApiUrl : pcApiUrl;
};

export default function SizePage() {
  const router = useRouter();
  const {
    gender: savedGender,
    setBodyMeasurements,
    setGender,
    predictedSize,
    setPredictedSize,
  } = useAppStore();
  const [hasMounted, setHasMounted] = useState(false);
  const [mode, setMode] = useState<PredictionMode>("camera");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [resultImage, setResultImage] = useState<string>("");
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [gender, setGenderState] = useState(savedGender || "Women");
  const [heightCm, setHeightCm] = useState("");
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [poseReady, setPoseReady] = useState(false);
  const [poseStatus, setPoseStatus] = useState(
    "Position yourself in view. We will check that your full body is visible.",
  );
  const [poseBox, setPoseBox] = useState<[number, number, number, number] | null>(
    null,
  );
  const [poseCheckVersion, setPoseCheckVersion] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    setHasMounted(true);
  }, []);

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraReady(false);
    setCameraOpen(false);
    setPoseReady(false);
    setPoseBox(null);
  };

  useEffect(() => {
    if (cameraOpen && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [cameraOpen]);

  useEffect(() => {
    const video = videoRef.current;
    const overlay = overlayRef.current;
    if (!video || !overlay || !cameraReady || !poseBox) {
      if (overlay) {
        overlay.width = 0;
        overlay.height = 0;
      }
      return;
    }

    const width = video.videoWidth;
    const height = video.videoHeight;
    if (!width || !height) return;

    overlay.width = width;
    overlay.height = height;
    const context = overlay.getContext("2d");
    if (!context) return;

    context.clearRect(0, 0, width, height);
    context.strokeStyle = "#facc15";
    context.lineWidth = Math.max(3, width * 0.006);
    context.shadowColor = "rgba(0, 0, 0, 0.75)";
    context.shadowBlur = Math.max(2, width * 0.004);
    context.strokeRect(
      poseBox[0] * width,
      poseBox[1] * height,
      (poseBox[2] - poseBox[0]) * width,
      (poseBox[3] - poseBox[1]) * height,
    );
  }, [cameraReady, poseBox]);

  // The version token deliberately restarts this polling effect on manual reset.
  // biome-ignore lint/correctness/useExhaustiveDependencies: used as an explicit polling restart trigger
  useEffect(() => {
    if (!cameraOpen || !cameraReady || mode !== "camera") return;

    let cancelled = false;
    let requestInProgress = false;
    let timer: number | undefined;
    let activeController: AbortController | null = null;
    let consecutiveReadyFrames = 0;
    let consecutiveUnreadyFrames = 0;
    let stableReady = false;

    const scheduleNextCheck = () => {
      if (!cancelled) {
        timer = window.setTimeout(
          () => void checkPose(),
          POSE_CHECK_INTERVAL_MS,
        );
      }
    };

    const checkPose = async () => {
      if (cancelled || requestInProgress) return;
      const video = videoRef.current;
      if (!video || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
        scheduleNextCheck();
        return;
      }

      requestInProgress = true;
      let requestTimeout: number | undefined;
      try {
        const frame = document.createElement("canvas");
        frame.width = video.videoWidth;
        frame.height = video.videoHeight;
        const context = frame.getContext("2d");
        if (!context) throw new Error("Unable to read the live camera frame.");
        context.drawImage(video, 0, 0, frame.width, frame.height);

        const blob = await new Promise<Blob | null>((resolve) =>
          frame.toBlob(resolve, "image/jpeg", 0.72),
        );
        if (cancelled) return;
        if (!blob) throw new Error("Unable to prepare the live camera frame.");

        const formData = new FormData();
        formData.append("file", blob, "live-camera-frame.jpg");
        const controller = new AbortController();
        activeController = controller;
        requestTimeout = window.setTimeout(
          () => controller.abort(),
          POSE_REQUEST_TIMEOUT_MS,
        );
        const response = await fetch(`${getApiBaseUrl()}/pose-readiness`, {
          method: "POST",
          body: formData,
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`Live pose check failed (${response.status}).`);
        }

        const result = (await response.json()) as PoseReadiness;
        if (cancelled) return;
        setPoseBox(result.box);
        const statusMessage =
          result.reason === "low_confidence"
            ? "Pose detected, but it is not clear enough yet. Face the camera, improve the lighting, and keep your whole body visible. Checking again automatically."
            : result.message;

        if (result.ready) {
          consecutiveReadyFrames += 1;
          consecutiveUnreadyFrames = 0;
          if (consecutiveReadyFrames >= 3) stableReady = true;
          setPoseReady(stableReady);
          setPoseStatus(
            stableReady
              ? statusMessage
              : "Hold still while we confirm your full-body position.",
          );
        } else {
          consecutiveReadyFrames = 0;
          if (
            result.reason === "partial" ||
            result.reason === "too_close" ||
            result.reason === "too_far" ||
            result.reason === "no_person"
          ) {
            consecutiveUnreadyFrames = 2;
          } else {
            consecutiveUnreadyFrames += 1;
          }
          if (consecutiveUnreadyFrames >= 2) stableReady = false;
          setPoseReady(stableReady);
          setPoseStatus(
            stableReady
              ? "Hold this position while the camera confirms your pose."
              : statusMessage,
          );
        }
      } catch (error: unknown) {
        if (!cancelled) {
          const isAbortError =
            error instanceof Error && error.name === "AbortError";
          if (!isAbortError) {
            console.error("Live pose check failed:", error);
          }
          consecutiveReadyFrames = 0;
          consecutiveUnreadyFrames += 1;
          if (consecutiveUnreadyFrames >= 2) stableReady = false;
          setPoseReady(stableReady);
          setPoseBox(null);
          setPoseStatus(
            isAbortError
              ? "The pose check timed out. Checking again automatically; please check the size-analysis server if this continues."
              : error instanceof TypeError
                ? `Could not reach the ${MODE} backend at ${getApiBaseUrl()}. Check that the backend is running and reachable from this device. On a phone, do not use localhost for a PC backend; use its network address or select MOBILE. Retrying automatically.`
                : "Unable to check your live pose. Check that the size-analysis server is running. Retrying automatically.",
          );
        }
      } finally {
        if (requestTimeout !== undefined) {
          window.clearTimeout(requestTimeout);
        }
        activeController = null;
        requestInProgress = false;
        scheduleNextCheck();
      }
    };

    void checkPose();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
      activeController?.abort();
    };
  }, [cameraOpen, cameraReady, mode, poseCheckVersion]);

  const resetPoseCheck = () => {
    setPoseReady(false);
    setPoseBox(null);
    setPoseStatus("Checking your pose...");
    setPoseCheckVersion((version) => version + 1);
  };

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, []);

  const openCamera = async () => {
    if (!window.isSecureContext) {
      setMessage(
        "Camera access requires a secure connection. Open the app at http://localhost:3000 or use an HTTPS address.",
      );
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setMessage("Camera access is not supported by this browser.");
      return;
    }

    try {
      let cameraStream: MediaStream;
      try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" } },
          audio: false,
        });
      } catch (preferredCameraError) {
        if (
          !(preferredCameraError instanceof DOMException) ||
          preferredCameraError.name !== "OverconstrainedError"
        ) {
          throw preferredCameraError;
        }

        cameraStream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      }

      streamRef.current = cameraStream;
      setMessage("");
      setCameraReady(false);
      setPoseReady(false);
      setPoseBox(null);
      setPoseStatus(
        "Please move back until you are approximately 2 metres away. Keep your entire body in the camera frame.",
      );
      setCameraOpen(true);
    } catch (error: unknown) {
      console.error("Unable to start camera:", error);
      const errorName = error instanceof DOMException ? error.name : "";
      const cameraErrorMessages: Record<string, string> = {
        NotAllowedError:
          "Camera permission was denied. Allow camera access for this site in your browser and check your device privacy settings, then try again.",
        NotFoundError:
          "No camera was found. Connect or enable a camera, or upload a photo instead.",
        NotReadableError:
          "The camera is already in use or unavailable. Close other apps using it and try again.",
        OverconstrainedError:
          "The camera could not start with the available settings. Try another camera or upload a photo instead.",
        SecurityError:
          "Camera access is blocked by browser or device security settings. Allow access for this site or upload a photo instead.",
      };
      setMessage(
        cameraErrorMessages[errorName] ??
          `Unable to start the camera${errorName ? ` (${errorName})` : ""}. Check browser and device camera permissions, or upload a photo instead.`,
      );
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    handleFile(f);
  };

  const handleFile = (f: File) => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResultImage("");
    setMeasurements([]);
    setPredictedSize(null);
    setMessage("");
  };

  const selectMode = (nextMode: PredictionMode) => {
    stopCamera();
    if (preview) URL.revokeObjectURL(preview);
    setMode(nextMode);
    setFile(null);
    setPreview("");
    setHeightCm("");
    setResultImage("");
    setMeasurements([]);
    setMessage("");
    setPredictedSize(null);
    setBodyMeasurements(null);
  };

  const capturePhoto = () => {
    if (!poseReady) {
      setPoseStatus("Wait until the full-body check confirms that you are ready.");
      return;
    }

    const video = videoRef.current;
    if (!video?.videoWidth || !video.videoHeight) {
      setMessage("The camera is not ready yet. Please wait a moment and try again.");
      return;
    }

    const canvas = document.createElement("canvas");
    const scale = Math.min(
      1,
      MAX_CAPTURE_DIMENSION / video.videoWidth,
      MAX_CAPTURE_DIMENSION / video.videoHeight,
    );
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    const context = canvas.getContext("2d");
    if (!context) {
      setMessage("Unable to capture an image from the camera.");
      return;
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (!blob) {
        setMessage("Unable to capture an image from the camera.");
        return;
      }
      const capturedPhoto = new File([blob], "camera-capture.jpg", {
        type: "image/jpeg",
      });
      handleFile(capturedPhoto);
      stopCamera();
      void handlePredict(capturedPhoto);
    }, "image/jpeg", CAPTURE_JPEG_QUALITY);
  };

  useEffect(() => {
    setGenderState(savedGender || "Women");
  }, [savedGender]);

  const updateGender = (nextGender: string) => {
    setGenderState(nextGender);
    setGender(nextGender);
  };

  const handlePredict = async (imageFile: File | null = file) => {
    if (!imageFile) {
      setMessage("Please select an image before predicting.");
      return;
    }

    if (!gender) {
      setMessage("Please select your gender for size estimation.");
      return;
    }

    const parsedHeight = heightCm.trim() ? Number(heightCm) : null;
    if (
      mode === "upload" &&
      parsedHeight !== null &&
      (!Number.isFinite(parsedHeight) || parsedHeight <= 0)
    ) {
      setMessage("Enter a valid height in centimeters, or leave it blank.");
      return;
    }

    const formData = new FormData();
    formData.append("file", imageFile);
    formData.append("mode", "automatic");
    formData.append("gender", gender);
    if (mode === "upload" && parsedHeight !== null) {
      formData.append("height", String(parsedHeight));
    }

    setLoading(true);
    setMessage("");

    try {
      const res = await fetch(`${getApiBaseUrl()}/predict`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData: unknown = await res.json().catch(() => null);
        const detail =
          typeof errorData === "object" &&
          errorData !== null &&
          "detail" in errorData &&
          typeof errorData.detail === "string"
            ? errorData.detail
            : `Prediction request failed (${res.status}).`;
        throw new Error(detail);
      }

      const data = (await res.json()) as {
        annotated_image?: string;
        measurements?: Measurement[];
      };
      const predictionMeasurements = data.measurements ?? [];
      const firstMeasurement = predictionMeasurements[0];

      setResultImage(data.annotated_image ?? "");
      setMeasurements(predictionMeasurements);
      setPredictedSize(firstMeasurement?.size ?? null);
      if (
        firstMeasurement?.size &&
        typeof firstMeasurement.height_cm === "number" &&
        Number.isFinite(firstMeasurement.height_cm) &&
        typeof firstMeasurement.shoulder_cm === "number" &&
        Number.isFinite(firstMeasurement.shoulder_cm) &&
        typeof firstMeasurement.hip_cm === "number" &&
        Number.isFinite(firstMeasurement.hip_cm)
      ) {
        setBodyMeasurements({
          heightCm: firstMeasurement.height_cm,
          shoulderCm: firstMeasurement.shoulder_cm,
          hipCm: firstMeasurement.hip_cm,
          gender,
          clothingSize: firstMeasurement.size,
        });
      } else {
        setBodyMeasurements(null);
      }

      if (predictionMeasurements.length === 0) {
        setMessage("No full-body pose was detected. Try a clear image with your full body in frame.");
      }
    } catch (err) {
      console.error(err);
      setMessage(
        err instanceof TypeError
          ? `Could not reach the ${MODE} prediction API at ${getApiBaseUrl()}. Check that the server is running and reachable from this device, then try again.`
          : err instanceof Error
            ? err.message
            : "Prediction failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-white text-[#111]">
      <nav className="flex items-center justify-between border-b border-[#e8e8e8] px-4 py-4 sm:px-8 sm:py-6 md:px-16">
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
              className="hidden text-sm tracking-[0.15em] text-[#111] transition-colors hover:text-[#888] md:block"
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
            className="hidden h-auto rounded-none bg-transparent p-0 text-sm tracking-[0.15em] text-[#111] hover:bg-transparent hover:text-[#888] md:block"
            style={{ ...SANS, fontWeight: 400 }}
          >
            LOGIN
          </Button>
          <Button
            onClick={() => router.push("/size")}
            variant="outline"
            size="sm"
            className="h-auto rounded-none border-[#111] px-2.5 py-1.5 text-xs tracking-[0.1em] text-[#111] transition-colors hover:bg-[#111] hover:text-white sm:px-4 sm:text-sm sm:tracking-[0.15em]"
            style={{ ...SANS, fontWeight: 400 }}
          >
            FIND YOUR SIZE
          </Button>
        </div>
      </nav>

      <main className="px-4 py-6 sm:px-8 sm:py-10 md:px-16 md:py-16">
        <div className="grid gap-6 lg:grid-cols-2">
          <motion.section
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className="overflow-hidden rounded-none border border-[#e8e8e8] bg-[#f7f4ee] shadow-[0_20px_80px_-30px_rgba(17,17,17,0.25)]"
          >
            <div className="relative h-full min-h-105 overflow-hidden rounded-none">
              <img
                src="/sizeHome.jpg"
                alt="Size measurement hero image"
                className="absolute inset-0 h-full w-full rounded-none object-cover object-top"
              />
              <div className="absolute inset-0 bg-linear-to-r from-black/70 via-black/20 to-transparent" />

              <div className="relative flex h-full flex-col justify-between p-8 sm:p-10 lg:p-12">
                <div className="max-w-xl">
                  <h1
                    className="text-4xl text-white sm:text-5xl lg:text-6xl"
                    style={{ ...SERIF, fontWeight: 300 }}
                  >
                    FIND YOUR SIZE
                  </h1>
                  <p
                    className="mt-4 max-w-lg text-sm leading-7 text-white/80 sm:text-base"
                    style={SANS}
                  >
                    Choose the camera or upload a full-body photo for a pixel-based size recommendation. Height is optional for centimeter measurements on uploads.
                  </p>
                  <div className="mt-8 flex flex-wrap gap-3">
                    <Button
                      onClick={() =>
                        document
                          .getElementById("size-analysis")
                          ?.scrollIntoView({ behavior: "smooth" })
                      }
                      className="flex items-center gap-2 rounded-none border border-white bg-white px-6 py-3 text-sm tracking-[0.12em] text-[#111] transition-all hover:bg-[#f2f2f2]"
                      style={{ ...SANS, fontWeight: 400 }}
                    >
                      START NOW
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      onClick={() => router.push("/")}
                      variant="ghost"
                      className="flex items-center gap-2 rounded-none border border-white/70 bg-transparent px-6 py-3 text-sm tracking-[0.12em] text-white transition-all hover:bg-white hover:text-[#111]"
                      style={{ ...SANS, fontWeight: 400 }}
                    >
                      BACK HOME
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </motion.section>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="border border-[#e8e8e8] bg-[#fafafa] p-4 sm:p-10 lg:p-12"
          >
            <h2
              className="text-2xl tracking-[0.2em] text-[#111]"
              style={{ ...SERIF, fontWeight: 400 }}
            >
              HOW IT WORKS
            </h2>
            <div className="mt-6 space-y-4">
              {[
                {
                  title: "CAMERA PREDICTION",
                  desc: <>Open the camera, stand approximately <strong className="bg-[#f4df70] px-1 font-bold text-[#111]">2 metres away</strong>, and capture a clear full-body photo. No height entry is needed.</>,
                },
                {
                  title: "UPLOAD A PHOTO",
                  desc: "Upload a clear full-body photo from about 2 metres away. Height is optional for centimeter measurements; size prediction uses pixel measurements.",
                },
                {
                  title: "RESULT",
                  desc: "Both options return your predicted clothing size.",
                },
              ].map((item) => (
                <div
                  key={item.title}
                  className="border-b border-[#e5e5e5] pb-4 last:border-b-0 last:pb-0"
                >
                  <p
                    className="text-sm tracking-[0.15em] text-[#777]"
                    style={SANS}
                  >
                    {item.title}
                  </p>
                  <p
                    className="mt-2 text-base leading-7 text-[#555]"
                    style={SANS}
                  >
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>

          <div
            id="size-analysis"
            className="border border-[#e8e8e8] bg-white p-4 sm:p-10 lg:p-12"
          >
            <div
              className="mb-4 flex items-center gap-2 text-sm tracking-[0.15em] text-[#555]"
              style={SANS}
            >
              START YOUR ANALYSIS
            </div>

            <div className="border border-[#e5e5e5] bg-[#fafafa] p-3 sm:p-7">
              <div className="grid gap-3 sm:grid-cols-2">
                {([
                  ["camera", "Use camera", "Live full-body guidance"],
                  ["upload", "Upload image", "Choose a full-body photo"],
                ] as const).map(([option, title, subtitle]) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => selectMode(option)}
                    aria-pressed={mode === option}
                    disabled={loading}
                    className={`border px-4 py-3 text-left transition disabled:cursor-not-allowed disabled:opacity-60 ${
                      mode === option
                        ? "border-[#111] bg-[#111] text-white"
                        : "border-[#d7d7d7] bg-white text-[#111] hover:border-[#999]"
                    }`}
                  >
                    <span className="block text-sm font-medium">{title}</span>
                    <span
                      className={`mt-1 block text-sm ${mode === option ? "text-white/80" : "text-[#666]"}`}
                    >
                      {subtitle}
                    </span>
                  </button>
                ))}
              </div>

              {mode === "camera" ? (
                <div className="mt-4">
                  <p
                    className="mb-3 border border-[#f0e3a2] bg-[#fff9df] px-4 py-3 font-sans text-base leading-7 text-[#666] sm:text-lg"
                  >
                    Please move back until you are approximately{" "}
                    <strong className="font-semibold text-[#111]">
                      2 metres away from the camera
                    </strong>
                    . The live pose check guides your framing and confirms that
                    your head, shoulders, hips, knees, and feet are visible. The
                    camera cannot verify the exact distance.
                  </p>
                  {cameraOpen ? (
                    <div className="border border-dashed border-[#d7d7d7] bg-white p-2 sm:p-3">
                      <div className="relative mx-auto h-[min(70svh,560px)] min-h-[360px] w-full overflow-hidden bg-black sm:aspect-video sm:h-auto sm:min-h-0">
                        <video
                          ref={videoRef}
                          autoPlay
                          playsInline
                          onLoadedMetadata={() => setCameraReady(true)}
                          className="absolute inset-0 h-full w-full object-contain"
                        />
                        <canvas
                          ref={overlayRef}
                          aria-hidden="true"
                          className="pointer-events-none absolute inset-0 h-full w-full object-contain"
                        />
                        <button
                          type="button"
                          onClick={resetPoseCheck}
                          disabled={!cameraReady}
                          aria-label="Reset pose check"
                          title="Reset pose check"
                          className="absolute right-3 top-3 z-10 rounded-md border border-white/30 bg-black/60 p-2 text-white transition hover:bg-black/80 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <Focus className="h-5 w-5" />
                        </button>
                      </div>
                      <p
                        role="status"
                        aria-live="polite"
                        className={`mt-3 border px-3 py-2 text-base leading-7 ${
                          poseReady
                            ? "border-[#d4e8d5] bg-[#f0f8f0] text-[#225b2a]"
                            : "border-[#f0e3a2] bg-[#fff9df] text-[#666]"
                        } font-sans`}
                      >
                        {poseStatus}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-3">
                        {poseReady && (
                          <button
                            type="button"
                            onClick={capturePhoto}
                            disabled={!cameraReady || loading}
                            className="flex-1 border border-[#111] bg-white px-4 py-2.5 text-base font-medium text-[#111] transition hover:bg-[#f5f5f5] disabled:cursor-not-allowed disabled:border-[#ddd] disabled:text-[#999]"
                          >
                            Capture Photo
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={stopCamera}
                          className="border border-[#d7d7d7] bg-white px-4 py-2.5 text-base text-[#555] transition hover:border-[#111] hover:text-[#111]"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={openCamera}
                      className="flex w-full cursor-pointer items-center justify-center gap-2 border border-dashed border-[#d7d7d7] bg-white px-4 py-8 text-center text-base font-medium text-[#111] transition hover:border-[#111] hover:bg-[#f5f5f5]"
                    >
                      <Camera className="h-4 w-4 text-[#777]" />
                      <span>Open camera for live full-body guidance</span>
                    </button>
                  )}
                </div>
              ) : (
                <label className="mt-4 flex cursor-pointer flex-col items-center justify-center border border-dashed border-[#d7d7d7] bg-white px-4 py-8 text-center transition hover:border-[#111] hover:bg-[#f5f5f5]">
                  <ImagePlus className="h-6 w-6 text-[#777]" />
                  <span className="mt-3 text-base font-medium text-[#111]">
                    Upload full-body image
                  </span>
                  <span className="mt-2 text-sm text-[#666]">
                    PNG, JPG, WEBP, and more
                  </span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleChange}
                    className="hidden"
                  />
                </label>
              )}

              {mode === "upload" && (
                <div className="mt-4">
                  <label
                    htmlFor="height-cm"
                    className="text-base font-medium text-[#111]"
                  >
                    Your height in centimeters (optional)
                  </label>
                  <input
                    id="height-cm"
                    type="number"
                    min="1"
                    step="0.1"
                    inputMode="decimal"
                    value={heightCm}
                    onChange={(event) => setHeightCm(event.target.value)}
                    placeholder="e.g. 170"
                    className="mt-2 w-full border border-[#d7d7d7] bg-white px-3 py-2.5 text-base text-[#111] outline-none focus:border-[#111]"
                  />
                  <p className="mt-3 border border-[#f0e3a2] bg-[#fff9df] px-4 py-3 font-sans text-base leading-7 text-[#666] sm:text-lg">
                    Take the photo from about 2 metres away. Height is used only
                    to scale the pixel measurements into centimeters; it does
                    not change the pixel-based size prediction. If left blank,
                    the app estimates height assuming a 2-metre distance and a
                    typical 60-degree camera field of view; actual results may
                    vary by camera and framing.
                  </p>
                </div>
              )}

              {file && (
                <div className="mt-3 truncate text-sm text-[#555]">
                  {file.name}
                </div>
              )}

              <div className="mt-5">
                <div className="text-base font-medium text-[#111]">Gender</div>
                <div className="mt-3 flex gap-3">
                  {["Women", "Men"].map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => updateGender(option)}
                      className={`rounded-none border px-4 py-2 text-sm tracking-[0.08em] transition-all ${
                        gender === option
                          ? "bg-[#111] text-white border-[#111]"
                          : "bg-white text-[#555] border-[#ddd] hover:border-[#999] hover:text-[#111]"
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={() => void handlePredict()}
                disabled={
                  loading ||
                  !file
                }
                className="mt-6 w-full rounded-none bg-[#111] px-4 py-3 text-sm tracking-[0.12em] text-white transition hover:bg-[#333] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "PROCESSING..." : "PREDICT SIZE"}
              </button>

              {message && (
                <p
                  className="mt-4 text-base leading-7 text-[#555]"
                  style={SANS}
                >
                  {message}
                </p>
              )}
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4 }}
            className="border border-[#e8e8e8] bg-white p-8"
          >
            <h3
              className="text-xl tracking-[0.2em] text-[#111]"
              style={{ ...SERIF, fontWeight: 400 }}
            >
              PREDICTED SIZE
            </h3>

            {measurements.length > 0 ? (
              <div className="mt-6 space-y-4">
                {measurements.map((m, i) => (
                  <div
                    key={`${m.size ?? "size"}-${i}`}
                    className="space-y-3"
                  >
                    <div className="border border-[#ddd] bg-[#fafafa] px-5 py-6 text-center">
                      <div
                        className="text-sm tracking-[0.12em] text-[#555]"
                        style={SANS}
                      >
                        RECOMMENDED CLOTHING SIZE
                      </div>
                      <div
                        className="mt-2 text-4xl text-[#111]"
                        style={{ ...SERIF, fontWeight: 500 }}
                      >
                        {m.size ?? "N/A"}
                      </div>
                    </div>
                  {m.height_cm !== undefined && (
                      <div className="grid grid-cols-3 border-y border-[#ddd]">
                        <div className="px-2 py-4 sm:px-4">
                          <p className="text-xs tracking-[0.08em] text-[#777]" style={SANS}>
                            SHOULDER WIDTH
                          </p>
                          <p className="mt-2 text-lg text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>
                            {m.shoulder_cm?.toFixed(1) ?? "—"} <span className="text-xs text-[#777]">cm</span>
                          </p>
                        </div>
                        <div className="border-l border-[#ddd] px-2 py-4 sm:px-4">
                          <p className="text-xs tracking-[0.08em] text-[#777]" style={SANS}>
                            HIP SIZE
                          </p>
                          <p className="mt-2 text-lg text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>
                            {m.hip_cm?.toFixed(1) ?? "—"} <span className="text-xs text-[#777]">cm</span>
                          </p>
                        </div>
                        <div className="border-l border-[#ddd] px-2 py-4 sm:px-4">
                          <p className="text-xs tracking-[0.08em] text-[#777]" style={SANS}>
                            {m.height_is_estimated ? "APPROX. HEIGHT" : "HEIGHT"}
                          </p>
                          <p className="mt-2 text-lg text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>
                            {m.height_cm.toFixed(1)} <span className="text-xs text-[#777]">cm</span>
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div
                className="mt-6 border border-dashed border-[#d7d7d7] bg-[#fafafa] p-6 text-base leading-7 text-[#555]"
                style={SANS}
              >
                Capture or upload a full-body photo to see your predicted size here.
              </div>
            )}
          </motion.div>
        </div>

        <section className="mt-10">
          <div className="space-y-6">
            {(preview || resultImage) && (
              <div className="grid gap-6 md:grid-cols-2">
                {preview && (
                  <motion.div
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="border border-[#e8e8e8] bg-white p-4"
                  >
                    <h3
                      className="text-lg tracking-[0.15em] text-[#111]"
                      style={{ ...SERIF, fontWeight: 500 }}
                    >
                      ORIGINAL
                    </h3>
                    <img
                      src={preview}
                      alt="Original upload preview"
                      className="mt-3 max-h-114 h-auto w-full object-contain"
                    />
                  </motion.div>
                )}

                {resultImage && (
                  <motion.div
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                    className="border border-[#e8e8e8] bg-white p-4"
                  >
                    <h3
                      className="text-lg tracking-[0.15em] text-[#111]"
                      style={{ ...SERIF, fontWeight: 500 }}
                    >
                      RESULT
                    </h3>
                    <img
                      src={resultImage}
                      alt="Annotated result"
                      className="mt-3 max-h-114 h-auto w-full object-contain"
                    />
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </section>

        {hasMounted && predictedSize && (
          <div className="mt-8 flex justify-center">
            <Button
              onClick={() => router.push("/health-tips")}
              className="h-auto flex items-center gap-2 rounded-none bg-[#111] px-4 py-3 text-sm tracking-[0.12em] text-white transition-colors hover:bg-[#333]"
              style={{ ...SANS, fontWeight: 400 }}
            >
              WELLNESS GUIDANCE
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </main>
    </div>
  );
}