// src/pages/LiveMonitoring.tsx
import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";

import { Camera, fetchCameras } from "@/lib/api";
import DashboardLayout from "@/components/DashboardLayout";

const LIVE_API_BASE =
  import.meta.env.VITE_LIVE_API_URL || "http://localhost:8001";
const LIVE_ENDPOINT = `${LIVE_API_BASE}/api/live/frame`;
const LIVE_CAMERA_ENDPOINT = `${LIVE_API_BASE}/api/live/camera/frame`;
const LOGS_LIST_ENDPOINT = `${LIVE_API_BASE}/api/logs/list`;
const LOGS_TAIL_ENDPOINT = `${LIVE_API_BASE}/api/logs/tail`;
const LOGS_DOWNLOAD_ENDPOINT = `${LIVE_API_BASE}/api/logs/download`;

type MonitoringMode = "webcam" | "cctv";

type LiveResult = {
  person: {
    name: string;
    phone: string;
    location: string;
    address: string;
    company: string;
    worker_id: number | null;
    location_id: number | null;
    company_id: number | null;
  };
  ppe: {
    helmet_on: boolean;
  };
  faces?: Array<{
    x: number;
    y: number;
    w: number;
    h: number;
    name?: string | null;
    ppe?: { helmet_on?: boolean };
  }>;
  frame_url?: string;
  timestamp?: string;
  camera_id?: number | null;
};

type WorkerRegisterModalProps = {
  open: boolean;
  onClose: () => void;
  faceBlob: Blob | null;
  onRegistered?: () => void;
};

const WorkerRegisterModal: React.FC<WorkerRegisterModalProps> = ({
  open,
  onClose,
  faceBlob,
  onRegistered,
}) => {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!faceBlob) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(faceBlob);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [faceBlob]);

  if (!open) return null;

  const handleSubmit = async () => {
    if (!faceBlob) {
      setError("No face image captured.");
      return;
    }
    try {
      setSubmitting(true);
      setError(null);

      const formData = new FormData();
      formData.append("face", faceBlob, "face.jpg");
      formData.append("name", name);
      formData.append("phone", phone);
      formData.append("company_id", companyId);
      formData.append("location_id", locationId);

      const res = await fetch(`${LIVE_API_BASE}/api/workers/register`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.error ?? "Failed to register worker.");
        return;
      }

      onRegistered?.();
      onClose();
      setName("");
      setPhone("");
      setCompanyId("");
      setLocationId("");
    } catch (err: any) {
      setError(err?.message ?? "Unexpected error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg border border-slate-200">
        <h2 className="text-lg font-semibold mb-1 text-slate-900">
          Register Unknown Person
        </h2>
        <p className="text-sm text-slate-600 mb-4">
          A new face was detected. Enter details to save this worker so VINIMI
          can recognize them next time.
        </p>

        {previewUrl && (
          <div className="mb-4 flex justify-center">
            <img
              src={previewUrl}
              alt="Captured face"
              className="max-h-48 rounded-lg border border-slate-200 object-contain shadow-sm"
            />
          </div>
        )}

        <div className="space-y-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Name</label>
            <input
              className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Worker name"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-500 mb-1">Phone</label>
            <input
              className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="Optional phone"
            />
          </div>

          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-xs text-slate-500 mb-1">
                Company ID
              </label>
              <input
                className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
                value={companyId}
                onChange={(e) => setCompanyId(e.target.value)}
                placeholder="e.g. 1"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs text-slate-500 mb-1">
                Location ID
              </label>
              <input
                className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500"
                value={locationId}
                onChange={(e) => setLocationId(e.target.value)}
                placeholder="e.g. 2"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-3 text-xs text-red-600 break-words">
            Error: {error}
          </div>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <button
            className="px-3 py-2 text-sm rounded-lg border border-slate-300 text-slate-700 bg-white hover:bg-slate-50"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            className="px-3 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium disabled:opacity-60 shadow-sm"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
};

const statusColor: Record<Camera["status"], string> = {
  online: "bg-emerald-400",
  offline: "bg-zinc-600",
  error: "bg-red-500",
  pending: "bg-amber-400",
};

const LiveMonitoring: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<number | null>(null);
  const lastFrameBlobRef = useRef<Blob | null>(null);
  const lastFrameSizeRef = useRef<{ width: number; height: number } | null>(null);
  const lastFrameImageUrlRef = useRef<string | null>(null);

  const [mode, setMode] = useState<MonitoringMode>("webcam");
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<string>("Idle");
  const [result, setResult] = useState<LiveResult | null>(null);

  const [registerModalOpen, setRegisterModalOpen] = useState(false);
  const [unknownFaceBlob, setUnknownFaceBlob] = useState<Blob | null>(null);

  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loadingCameras, setLoadingCameras] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [selectedCameraId, setSelectedCameraId] = useState<number | null>(null);
  const [cctvFrameUrl, setCctvFrameUrl] = useState<string | null>(null);
  const [logFiles, setLogFiles] = useState<string[]>([]);
  const [selectedLogFile, setSelectedLogFile] = useState<string | null>(null);
  const [logRows, setLogRows] = useState<any[]>([]);
  const [autoRefreshLogs, setAutoRefreshLogs] = useState(true);

  // start camera
  const startCamera = useCallback(async () => {
    if (streamRef.current) return;
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });
    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
    }
  }, []);

  const stopMonitoring = useCallback(() => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    // clear overlay
    const overlay = overlayRef.current;
    const ctx = overlay?.getContext("2d");
    if (overlay && ctx) {
      ctx.clearRect(0, 0, overlay.width, overlay.height);
    }
    setResult(null);
    setCctvFrameUrl(null);
    setRunning(false);
  }, []);

  useEffect(() => stopMonitoring, [stopMonitoring]);

  const captureAndSendFrame = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    if (!video.videoWidth || !video.videoHeight) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const targetWidth = 640;
    const scale = targetWidth / video.videoWidth;
    const targetHeight = Math.round(video.videoHeight * scale);

    canvas.width = targetWidth;
    canvas.height = targetHeight;
    ctx.drawImage(video, 0, 0, targetWidth, targetHeight);

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob((b) => resolve(b), "image/jpeg", 0.7)
    );
    if (!blob) return;

    lastFrameBlobRef.current = blob;
    lastFrameImageUrlRef.current = null;
    lastFrameSizeRef.current = { width: targetWidth, height: targetHeight };

    const formData = new FormData();
    formData.append("file", blob, "frame.jpg");

    try {
      const resp = await fetch(LIVE_ENDPOINT, {
        method: "POST",
        body: formData,
      });

      if (!resp.ok) {
        setStatus(`Error: ${resp.status} ${resp.statusText}`);
        return;
      }

      const data = (await resp.json()) as LiveResult;
      setResult(data);
      setStatus("OK");
    } catch (err: any) {
      setStatus(`Error: ${err?.message ?? String(err)}`);
    }
  }, []);

  const pollCctvFrame = useCallback(async () => {
    if (!selectedCameraId) {
      setStatus("Select a camera to start");
      return;
    }
    try {
      const resp = await fetch(LIVE_CAMERA_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ camera_id: selectedCameraId }),
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || `HTTP ${resp.status}`);
      }

      const data = (await resp.json()) as LiveResult;
      setResult(data);
      setStatus(`Camera ${selectedCameraId} OK`);

      if (data.frame_url) {
        const busted = data.frame_url.includes("?")
          ? `${data.frame_url}&t=${Date.now()}`
          : `${data.frame_url}?t=${Date.now()}`;
        setCctvFrameUrl(busted);
        lastFrameImageUrlRef.current = busted;
        lastFrameBlobRef.current = null;

        const img = new Image();
        img.onload = () => {
          lastFrameSizeRef.current = {
            width: img.naturalWidth,
            height: img.naturalHeight,
          };
        };
        img.src = busted;
      }
    } catch (err: any) {
      setStatus(`Camera error: ${err?.message ?? String(err)}`);
    }
  }, [selectedCameraId]);

  const startWebcamMonitoring = useCallback(async () => {
    await startCamera();
    setRunning(true);
    setStatus("Camera started. Sending frames…");
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
    }
    intervalRef.current = window.setInterval(captureAndSendFrame, 4000);
  }, [captureAndSendFrame, startCamera]);

  const startCctvMonitoring = useCallback(async () => {
    if (!selectedCameraId) {
      setStatus("Select a camera to start");
      return;
    }
    setRunning(true);
    setStatus("Polling camera…");
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
    }
    await pollCctvFrame();
    intervalRef.current = window.setInterval(pollCctvFrame, 4000);
  }, [pollCctvFrame, selectedCameraId]);

  const handleStart = useCallback(async () => {
    stopMonitoring();
    try {
      if (mode === "webcam") {
        await startWebcamMonitoring();
      } else {
        await startCctvMonitoring();
      }
    } catch (err: any) {
      setStatus(`Start error: ${err?.message ?? String(err)}`);
      setRunning(false);
    }
  }, [mode, startCctvMonitoring, startWebcamMonitoring, stopMonitoring]);

  const handleStop = useCallback(() => {
    stopMonitoring();
    setStatus("Stopped");
  }, [stopMonitoring]);

  const fetchLogs = useCallback(async (file?: string) => {
    const targetFile = file ?? selectedLogFile;
    try {
      const params = new URLSearchParams();
      if (targetFile) params.set("file", targetFile);
      params.set("lines", "200");
      const res = await fetch(`${LOGS_TAIL_ENDPOINT}?${params.toString()}`);
      if (!res.ok) {
        setLogRows([]);
        return;
      }
      const rows = await res.json();
      if (Array.isArray(rows)) {
        setLogRows(rows);
      }
    } catch {
      setLogRows([]);
    }
  }, [selectedLogFile]);

  const fetchLogFiles = useCallback(async () => {
    try {
      const res = await fetch(LOGS_LIST_ENDPOINT);
      const files = await res.json();
      if (Array.isArray(files)) {
        setLogFiles(files);
        if (!selectedLogFile && files.length > 0) {
          const today = new Date().toISOString().slice(0, 10) + ".log";
          const dateFile =
            files.find((f: string) => f === today) ||
            files.find((f: string) => /^\d{4}-\d{2}-\d{2}\.log$/.test(f)) ||
            files[0];
          setSelectedLogFile(dateFile);
          void fetchLogs(dateFile);
        }
      }
    } catch {
      // ignore
    }
  }, [selectedLogFile, fetchLogs]);

  useEffect(() => {
    stopMonitoring();
    setResult(null);
    setCctvFrameUrl(null);
    lastFrameBlobRef.current = null;
    lastFrameImageUrlRef.current = null;
    setStatus("Idle");
  }, [mode, stopMonitoring]);

  useEffect(() => {
    void fetchLogFiles();
  }, [fetchLogFiles]);

  useEffect(() => {
    void fetchLogs();
    if (!autoRefreshLogs) return;
    const id = window.setInterval(() => {
      void fetchLogs();
    }, 4000);
    return () => window.clearInterval(id);
  }, [fetchLogs, autoRefreshLogs, selectedLogFile]);

  useEffect(() => {
    if (mode !== "cctv") return;
    setLoadingCameras(true);
    setCameraError(null);
    fetchCameras(1)
      .then((cams) => {
        setCameras(cams);
        const preferred =
          cams.find((c) => c.status === "online") ?? cams[0] ?? null;
        setSelectedCameraId((prev) => prev ?? preferred?.id ?? null);
      })
      .catch((err) => {
        console.error(err);
        setCameraError(err?.message ?? "Failed to load cameras");
        setCameras([]);
      })
      .finally(() => setLoadingCameras(false));
  }, [mode]);

  useEffect(() => {
    if (mode === "cctv" && running) {
      stopMonitoring();
      setTimeout(() => {
        void startCctvMonitoring();
      }, 50);
    }
  }, [mode, running, startCctvMonitoring, stopMonitoring, selectedCameraId]);

  useEffect(() => {
    const overlay = overlayRef.current;
    const baseEl = mode === "webcam" ? videoRef.current : imageRef.current;
    if (!overlay || !baseEl) return;

    const ctx = overlay.getContext("2d");
    if (!ctx) return;

    const rect = baseEl.getBoundingClientRect();
    overlay.width = rect.width;
    overlay.height = rect.height;
    overlay.style.width = `${rect.width}px`;
    overlay.style.height = `${rect.height}px`;

    ctx.clearRect(0, 0, overlay.width, overlay.height);

    if (!result || !lastFrameSizeRef.current) {
      return;
    }

    const srcW = lastFrameSizeRef.current.width;
    const srcH = lastFrameSizeRef.current.height;
    if (!srcW || !srcH) return;

    const scaleX = overlay.width / srcW;
    const scaleY = overlay.height / srcH;

    const faces = result.faces || [];
    faces.forEach((f) => {
      const x = Math.round(f.x * scaleX);
      const y = Math.round(f.y * scaleY);
      const w = Math.round(f.w * scaleX);
      const h = Math.round(f.h * scaleY);

      const helmetOn = f.ppe?.helmet_on ?? result.ppe.helmet_on;
      const recognized =
        f.name && f.name.toLowerCase() !== "unknown" && f.name.trim().length > 0;
      const boxColor = recognized ? "#22c55e" : "#ef4444";
      const fillColor = recognized
        ? "rgba(34,197,94,0.2)"
        : "rgba(239,68,68,0.18)";

      ctx.lineWidth = 3;
      ctx.strokeStyle = boxColor;
      ctx.fillStyle = fillColor;

      ctx.fillRect(x, y, w, h);
      ctx.strokeRect(x, y, w, h);

      const label =
        f.name && f.name.toLowerCase() !== "unknown" ? f.name : "Unknown";
      ctx.font = "14px system-ui, sans-serif";
      ctx.textBaseline = "top";
      const textW = ctx.measureText(label).width + 10;

      ctx.fillStyle = "rgba(0,0,0,0.7)";
      ctx.fillRect(x, Math.max(0, y - 22), textW, 20);

      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, x + 5, Math.max(0, y - 19));

      // Helmet emoji overlay on box
      const emoji = helmetOn ? "✅" : "❌";
      ctx.font = "18px system-ui, sans-serif";
      ctx.textBaseline = "top";
      ctx.fillText(emoji, Math.min(overlay.width - 20, x + w - 18), Math.max(0, y - 22));
    });

    // If no faces, show a small badge in top-right based on helmet_on status (if available)
    if (faces.length === 0 && result.ppe) {
      const emoji = result.ppe.helmet_on ? "✅" : "❌";
      ctx.font = "18px system-ui, sans-serif";
      ctx.textBaseline = "top";
      ctx.fillStyle = "#ffffff";
      ctx.fillText(emoji, overlay.width - 22, 6);
    }
  }, [mode, result, cctvFrameUrl]);

  // triple-click handler on overlay canvas to register unknown
  const clickCountRef = useRef(0);
  const clickTimerRef = useRef<number | null>(null);

  const getCurrentFrameBlob = useCallback(async (): Promise<Blob | null> => {
    if (mode === "webcam") {
      return lastFrameBlobRef.current;
    }
    const url = lastFrameImageUrlRef.current;
    if (!url) return null;
    try {
      const resp = await fetch(url, { cache: "no-store" });
      if (!resp.ok) return null;
      return await resp.blob();
    } catch {
      return null;
    }
  }, [mode]);

  const handleOverlayClick = async () => {
    clickCountRef.current += 1;
    if (clickTimerRef.current) {
      window.clearTimeout(clickTimerRef.current);
    }
    clickTimerRef.current = window.setTimeout(() => {
      clickCountRef.current = 0;
      clickTimerRef.current = null;
    }, 800);

    if (clickCountRef.current >= 3) {
      clickCountRef.current = 0;
      if (clickTimerRef.current) {
        window.clearTimeout(clickTimerRef.current);
        clickTimerRef.current = null;
      }

      const unknownFace = result?.faces?.find(
        (f) => !f.name || f.name.toLowerCase() === "unknown"
      );

      if (!unknownFace || !lastFrameSizeRef.current) {
        setStatus("No unknown face detected in the latest frame.");
        return;
      }

      const frameBlob = await getCurrentFrameBlob();
      if (!frameBlob) {
        setStatus("No frame available to capture face.");
        return;
      }

      try {
        const cropped = await new Promise<Blob | null>((resolve) => {
          const img = new Image();
          const url = URL.createObjectURL(frameBlob);
          img.onload = () => {
            const off = document.createElement("canvas");
            off.width = Math.max(1, Math.round(unknownFace.w));
            off.height = Math.max(1, Math.round(unknownFace.h));
            const octx = off.getContext("2d");
            if (!octx) {
              URL.revokeObjectURL(url);
              resolve(null);
              return;
            }
            octx.drawImage(
              img,
              unknownFace.x,
              unknownFace.y,
              unknownFace.w,
              unknownFace.h,
              0,
              0,
              off.width,
              off.height
            );
            off.toBlob((b) => {
              URL.revokeObjectURL(url);
              resolve(b);
            }, "image/jpeg", 0.9);
          };
          img.onerror = () => {
            URL.revokeObjectURL(url);
            resolve(null);
          };
          img.src = url;
        });

        setUnknownFaceBlob(cropped);
        setRegisterModalOpen(true);
      } catch (err) {
        console.error(err);
        setUnknownFaceBlob(frameBlob);
        setRegisterModalOpen(true);
      }
    }
  };

  const handleModalClose = () => {
    setRegisterModalOpen(false);
    setUnknownFaceBlob(null);
  };

  const handleRegistered = () => {
    setUnknownFaceBlob(null);
  };

  const personLabel =
    result?.person?.name && result.person.name.toLowerCase() !== "unknown"
      ? result.person.name
      : "Unknown";

  const formatTime = (iso: string | undefined) => {
    if (!iso) return "–";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso);
    const now = new Date();
    const opts: Intl.DateTimeFormatOptions = {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    };
    if (d.toDateString() !== now.toDateString()) {
      opts.month = "short";
      opts.day = "2-digit";
    }
    return new Intl.DateTimeFormat(undefined, opts).format(d);
  };

  const handleDownload = (fmt: "csv" | "json" | "pdf") => {
    const params = new URLSearchParams();
    if (selectedLogFile) params.set("file", selectedLogFile);
    params.set("format", fmt);
    const url = `${LOGS_DOWNLOAD_ENDPOINT}?${params.toString()}`;
    window.open(url, "_blank");
  };

const renderModeToggle = (
  <div className="flex items-center gap-2 text-sm">
    <span className="text-slate-500 text-xs uppercase tracking-[0.3em]">
      Source
    </span>
    {(["webcam", "cctv"] as MonitoringMode[]).map((m) => (
      <button
        key={m}
        onClick={() => setMode(m)}
        className={`px-3 py-1 rounded-md border text-xs font-medium transition ${
          mode === m
            ? "border-blue-600 bg-blue-50 text-blue-700"
            : "border-slate-300 text-slate-700 hover:border-slate-400 hover:bg-slate-50"
        }`}
      >
        {m === "webcam" ? "Webcam" : "CCTV"}
      </button>
    ))}
  </div>
);

  const renderCameraSelect = (
    <div className="flex items-center gap-3">
      <Select
        value={selectedCameraId ? String(selectedCameraId) : undefined}
        onValueChange={(value) => setSelectedCameraId(Number(value))}
        disabled={loadingCameras || cameras.length === 0}
      >
        <SelectTrigger className="w-52 bg-white border-slate-300 text-slate-800">
          <SelectValue
            placeholder={
              loadingCameras ? "Loading cameras…" : "Select camera"
            }
          />
        </SelectTrigger>
        <SelectContent className="bg-white border-slate-200 text-slate-800 shadow-md">
          {cameras.map((cam) => (
            <SelectItem key={cam.id} value={String(cam.id)}>
              <span className="inline-flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${statusColor[cam.status]}`}
                />
                {cam.name}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {selectedCameraId && (
        <span className="inline-flex items-center gap-1 text-xs text-slate-500">
          <span
            className={`h-2 w-2 rounded-full ${
              statusColor[
                cameras.find((c) => c.id === selectedCameraId)?.status ||
                  "offline"
              ]
            }`}
          />
          {cameras.find((c) => c.id === selectedCameraId)?.status ?? "unknown"}
        </span>
      )}
    </div>
  );

  const content = (
    <div className="h-full flex flex-col max-w-7xl mx-auto">
      <div className="px-6 pt-4 pb-3 border-b border-slate-200 bg-white/90 backdrop-blur flex flex-wrap gap-4 items-center justify-between rounded-t-xl shadow-sm">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
            <span role="img" aria-label="camera">
              📷
            </span>
            Live Monitoring
          </h1>
          <p className="text-xs text-slate-600 mt-1">
            {mode === "webcam"
              ? `Uses your webcam and posts frames to ${LIVE_ENDPOINT}`
              : `Polling cameras through ${LIVE_CAMERA_ENDPOINT}`}
          </p>
          {personLabel === "Unknown" && (
            <p className="text-[11px] text-amber-600 mt-1">
              Unknown person detected – triple-click on the video to register.
            </p>
          )}
        </div>
        <div className="flex flex-col gap-2">
          {renderModeToggle}
          {mode === "cctv" && (
            <div className="flex items-center gap-3">
              {renderCameraSelect}
              {cameraError && (
                <span className="text-xs text-red-400">{cameraError}</span>
              )}
            </div>
          )}
        </div>
        <div className="flex gap-2 ml-auto">
          <button
            onClick={handleStart}
            disabled={running}
            className="px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-50 shadow-sm"
          >
            {running ? "Running…" : "Start"}
          </button>
          <button
            onClick={handleStop}
            className="px-4 py-1.5 rounded-md bg-white border border-slate-300 text-sm text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            Stop
          </button>
        </div>
      </div>

      <div className="flex-1 px-6 py-4 flex flex-col gap-4">
        <div className="flex-1 flex items-center justify-center rounded-xl overflow-hidden border border-slate-200 bg-white transition-all shadow-sm">
          <div className="w-full max-w-4xl aspect-video bg-slate-200 flex items-center justify-center relative">
            {mode === "webcam" ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full h-full object-contain bg-slate-200"
              />
            ) : cctvFrameUrl ? (
              <img
                ref={imageRef}
                src={cctvFrameUrl}
                alt="CCTV frame"
                className="w-full h-full object-contain bg-slate-200"
              />
            ) : (
              <div className="text-sm text-slate-500">No frame yet</div>
            )}
            <canvas ref={canvasRef} className="hidden" />
            <canvas
              ref={overlayRef}
              className="absolute inset-0 pointer-events-auto"
              onClick={handleOverlayClick}
            />
            {result && (
              <div className="absolute top-3 left-3 bg-black/60 text-white text-sm px-2 py-1 rounded-md pointer-events-none">
                {personLabel}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-4 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Live Logs</h3>
              <p className="text-xs text-slate-500">Showing last 200 entries</p>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <Select
                value={selectedLogFile || undefined}
                onValueChange={(v) => setSelectedLogFile(v)}
              >
                <SelectTrigger className="w-56 bg-white border-slate-300 text-slate-800">
                  <SelectValue placeholder="Select log file" />
                </SelectTrigger>
                <SelectContent className="bg-white border-slate-200 text-slate-800 max-h-60">
                  {logFiles.length === 0 && (
                    <SelectItem value="none" disabled>
                      No logs available
                    </SelectItem>
                  )}
                  {logFiles.map((f) => (
                    <SelectItem key={f} value={f}>
                      {f}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Switch
                  checked={autoRefreshLogs}
                  onCheckedChange={(v) => setAutoRefreshLogs(v)}
                />
                Auto refresh (4s)
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => fetchLogs()}>
                  Refresh
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleDownload("csv")}>
                  CSV
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleDownload("json")}>
                  JSON
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleDownload("pdf")}>
                  PDF
                </Button>
              </div>
            </div>
          </div>

          <div className="max-h-80 overflow-auto rounded-lg border border-slate-200">
            <table className="w-full text-sm text-slate-800">
              <thead className="bg-slate-100 sticky top-0 z-10">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 border-b border-slate-200">Time</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 border-b border-slate-200">Name</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 border-b border-slate-200">Worker</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 border-b border-slate-200">Loc</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 border-b border-slate-200">Helmet</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 border-b border-slate-200">Status</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 border-b border-slate-200">Sim.</th>
                </tr>
              </thead>
              <tbody>
                {logRows.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-3 py-3 text-center text-slate-500">
                      No logs for selected date.
                    </td>
                  </tr>
                ) : (
                  logRows.map((row, idx) => {
                    const helmet = row.helmet_on === true;
                    const unknown = row.is_unknown === true;
                    return (
                      <tr key={idx} className={`${unknown ? "text-slate-500" : "text-slate-900"}`}>
                        <td className="px-3 py-2 border-b border-slate-200">{formatTime(row.ts)}</td>
                        <td className="px-3 py-2 border-b border-slate-200">{row.name || "Unknown"}</td>
                        <td className="px-3 py-2 border-b border-slate-200">{row.worker_id ?? "–"}</td>
                        <td className="px-3 py-2 border-b border-slate-200">{row.location_id ?? "–"}</td>
                        <td className="px-3 py-2 border-b border-slate-200">{helmet ? "✅" : "❌"}</td>
                        <td className={`px-3 py-2 border-b border-slate-200 ${!helmet ? "text-red-500" : ""}`}>
                          {unknown ? "Unknown" : "Recognized"}
                        </td>
                        <td className="px-3 py-2 border-b border-slate-200">
                          {row.similarity != null ? Number(row.similarity).toFixed(3) : "–"}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <WorkerRegisterModal
        open={registerModalOpen}
        onClose={handleModalClose}
        faceBlob={unknownFaceBlob}
        onRegistered={handleRegistered}
      />
    </div>
  );
  return <DashboardLayout title="Live Monitoring">{content}</DashboardLayout>;
};

export default LiveMonitoring;
