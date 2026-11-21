"use client";

import React, { useState, useEffect, useCallback } from "react";
import { 
  Play, Sparkles, Youtube, CheckCircle2, Clock, 
  Layers, Volume2, ShieldCheck, Share2, UploadCloud, 
  TrendingUp, Copy, Check, AlertCircle, RefreshCw,
  Settings, ExternalLink, Globe, Server, CheckCircle, XCircle,
  Image as ImageIcon, Download, Eye
} from "lucide-react";

interface VideoInfo {
  id: string;
  title: string;
  duration: number;
  uploader: string;
  thumbnail: string;
  is_live: boolean;
  was_live: boolean;
}

interface Clip {
  clip_id: string;
  clip_index: number;
  relative_video_path: string;
  thumbnails?: {
    vertical?: string;
    landscape?: string;
  };
  start: number;
  end: number;
  duration: number;
  text: string;
  virality_rate: number;
  virality_breakdown: {
    hook_strength: number;
    emotional_intensity: number;
    narrative_flow: number;
    rewatchability: number;
  };
  title: string;
  suggested_titles: string[];
  description: string;
  hashtags: string[];
  layout_mode: string;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [targetDuration, setTargetDuration] = useState<number>(30);
  const [maxClips, setMaxClips] = useState<number>(3);
  const [splitScreen, setSplitScreen] = useState<boolean>(true);
  const [showWatermark, setShowWatermark] = useState<boolean>(false);
  const [showHeadline, setShowHeadline] = useState<boolean>(true);
  const [showCaptions, setShowCaptions] = useState<boolean>(true);
  
  // Status states
  const [isFetchingInfo, setIsFetchingInfo] = useState(false);
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressStep, setProgressStep] = useState<string>("");
  const [clips, setClips] = useState<Clip[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Backend Engine Config & Health State
  const [backendUrl, setBackendUrl] = useState<string>("");
  const [customInputUrl, setCustomInputUrl] = useState<string>("");
  const [backendStatus, setBackendStatus] = useState<"checking" | "connected" | "disconnected">("checking");
  const [engineInfo, setEngineInfo] = useState<{ device?: string; whisper_model?: string } | null>(null);
  const [showSettingsModal, setShowSettingsModal] = useState<boolean>(false);
  const [isCheckingHealth, setIsCheckingHealth] = useState<boolean>(false);
  const [isVercelEnv, setIsVercelEnv] = useState<boolean>(false);

  // Modal / Antigravity posting state
  const [activePostModal, setActivePostModal] = useState<Clip | null>(null);
  const [antigravityPosting, setAntigravityPosting] = useState(false);
  const [previewModes, setPreviewModes] = useState<Record<string, "video" | "thumb_vert" | "thumb_land">>({});

  // Initialize backend URL based on environment
  useEffect(() => {
    if (typeof window !== "undefined") {
      const isVercel = window.location.hostname.includes("vercel.app");
      setIsVercelEnv(isVercel);

      const savedUrl = localStorage.getItem("autoclip_backend_url");
      if (savedUrl) {
        setBackendUrl(savedUrl);
        setCustomInputUrl(savedUrl);
      } else if (isVercel) {
        // On Vercel, localhost rewrites fail due to DNS_HOSTNAME_RESOLVED_PRIVATE
        // Leave backendUrl empty so user can configure tunnel or run locally
        setBackendUrl("");
        setCustomInputUrl("http://localhost:8000");
      } else {
        // Running locally (e.g. localhost:3000)
        setBackendUrl("http://localhost:8000");
        setCustomInputUrl("http://localhost:8000");
      }
    }
  }, []);

  // Compute the effective URL to talk to the backend
  const getEffectiveBackendUrl = useCallback(() => {
    if (backendUrl.trim()) {
      return backendUrl.trim().replace(/\/$/, "");
    }
    if (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) {
      return "http://localhost:8000";
    }
    // Fallback relative path on local dev proxy
    return "";
  }, [backendUrl]);

  // Health check helper
  const checkHealth = useCallback(async (targetUrl?: string) => {
    setIsCheckingHealth(true);
    const base = targetUrl !== undefined ? targetUrl.trim().replace(/\/$/, "") : getEffectiveBackendUrl();
    const endpoint = base ? `${base}/api/health` : "/api/backend/health";

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      
      const res = await fetch(endpoint, {
        method: "GET",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      const contentType = res.headers.get("content-type") || "";
      if (res.ok && contentType.includes("application/json")) {
        const data = await res.json();
        if (data.status === "healthy") {
          setBackendStatus("connected");
          setEngineInfo({ device: data.device, whisper_model: data.whisper_model });
          setIsCheckingHealth(false);
          return true;
        }
      }
      setBackendStatus("disconnected");
      setEngineInfo(null);
      setIsCheckingHealth(false);
      return false;
    } catch (err) {
      setBackendStatus("disconnected");
      setEngineInfo(null);
      setIsCheckingHealth(false);
      return false;
    }
  }, [getEffectiveBackendUrl]);

  // Run health check whenever backendUrl changes
  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Safe API request wrapper that never crashes with raw JSON SyntaxErrors
  const safeApiRequest = async (path: string, options?: RequestInit) => {
    const base = getEffectiveBackendUrl();
    let urlToFetch = "";

    if (base) {
      const cleanPath = path.startsWith("/") ? path : `/${path}`;
      urlToFetch = `${base}${cleanPath}`;
    } else {
      // Relative path fallback (e.g. Next.js rewrite /api/backend/...)
      const cleanPath = path.replace(/^\/api/, "");
      urlToFetch = `/api/backend${cleanPath}`;
    }

    let res: Response;
    try {
      res = await fetch(urlToFetch, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...(options?.headers || {}),
        },
      });
    } catch (networkErr: any) {
      const isVercel = typeof window !== "undefined" && window.location.hostname.includes("vercel.app");
      if (isVercel) {
        throw new Error(
          "Cannot connect to AutoClip AI engine from Vercel. Browsers block HTTPS to http://localhost requests (Mixed Content), and Vercel cannot reach your local machine. Please run AutoClip Pro locally at http://localhost:3000 via 'start_frontend.bat', or enter an HTTPS tunnel URL in Engine Settings."
        );
      }
      throw new Error(`Cannot reach backend engine at ${base || "http://localhost:8000"}. Please make sure 'start_backend.bat' is running.`);
    }

    const contentType = res.headers.get("content-type") || "";

    if (!res.ok) {
      if (contentType.includes("application/json")) {
        const errJson = await res.json();
        throw new Error(errJson.detail || errJson.message || `Backend error: ${res.statusText}`);
      } else {
        const textResponse = await res.text();
        if (textResponse.includes("DNS_HOSTNAME_RESOLVED_PRIVATE") || textResponse.includes("The page could not be found")) {
          throw new Error(
            "Vercel Cloud Proxy Error: Vercel serverless cannot reach your local machine's port 8000 (DNS_HOSTNAME_RESOLVED_PRIVATE). To generate clips with your local GPU/CPU, launch the frontend locally at http://localhost:3000 by running 'start_frontend.bat'."
          );
        }
        throw new Error(`Backend service error (${res.status}): ${textResponse.slice(0, 140)}`);
      }
    }

    if (!contentType.includes("application/json")) {
      const textResponse = await res.text();
      throw new Error(`Invalid response format from server: ${textResponse.slice(0, 120)}`);
    }

    return await res.json();
  };

  const handleSaveSettings = async () => {
    const cleanUrl = customInputUrl.trim().replace(/\/$/, "");
    setBackendUrl(cleanUrl);
    if (typeof window !== "undefined") {
      localStorage.setItem("autoclip_backend_url", cleanUrl);
    }
    const isOk = await checkHealth(cleanUrl);
    if (isOk) {
      setShowSettingsModal(false);
      setError(null);
    }
  };

  const fetchVideoInfo = async () => {
    if (!url.trim()) return;
    setIsFetchingInfo(true);
    setError(null);

    try {
      const data = await safeApiRequest("/api/info", {
        method: "POST",
        body: JSON.stringify({ url }),
      });

      if (data.success && data.info) {
        setVideoInfo(data.info);
      } else {
        setError(data.detail || "Failed to load video information");
      }
    } catch (err: any) {
      setError(err.message || "Cannot connect to backend service.");
    } finally {
      setIsFetchingInfo(false);
    }
  };

  const startClipping = async () => {
    if (!url.trim()) return;
    setIsProcessing(true);
    setError(null);
    setProgressStep("Initializing pipeline & downloading media stream...");

    try {
      const data = await safeApiRequest("/api/clip", {
        method: "POST",
        body: JSON.stringify({
          url,
          target_duration: targetDuration,
          max_clips: maxClips,
          force_split_screen: splitScreen,
          show_watermark: showWatermark,
          show_headline: showHeadline,
          show_captions: showCaptions,
        }),
      });

      if (data.success && data.data) {
        setClips(data.data.clips || []);
        if (data.data.video_info) {
          setVideoInfo(data.data.video_info);
        }
      } else {
        setError(data.detail || "Video clipping pipeline encountered an issue.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to communicate with processing engine.");
    } finally {
      setIsProcessing(false);
      setProgressStep("");
    }
  };

  const handleAntigravityUpload = async (clip: Clip) => {
    setAntigravityPosting(true);
    try {
      const data = await safeApiRequest("/api/antigravity/prepare_post", {
        method: "POST",
        body: JSON.stringify({
          clip_id: clip.clip_id,
          title: clip.title,
          description: clip.description,
          tags: clip.hashtags,
          visibility: "public"
        })
      });
      if (data.success) {
        alert("🚀 Antigravity Agent Dispatched!\n\nAntigravity is now controlling Chrome & CMD to upload this Short directly to YouTube Studio without hitting API quota limits!");
        setActivePostModal(null);
      }
    } catch (err: any) {
      alert(`Error triggering Antigravity agent: ${err.message}`);
    } finally {
      setAntigravityPosting(false);
    }
  };

  // Video source base path
  const videoBaseUrl = getEffectiveBackendUrl() || "http://localhost:8000";

  return (
    <div className="min-h-screen bg-[#090A0F] text-white flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-[#1E2235] px-6 py-4 flex flex-wrap items-center justify-between gap-3 bg-[#12141D]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              AutoClip <span className="text-indigo-400">Pro</span>
            </span>
            <span className="text-xs ml-2 px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {isVercelEnv ? "v1.0 Vercel Edition" : "v1.0 Local Master"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Real Backend Engine Status Pill */}
          <button
            onClick={() => setShowSettingsModal(true)}
            className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border transition hover:opacity-85 ${
              backendStatus === "connected"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : backendStatus === "checking"
                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                : "bg-red-500/10 text-red-400 border-red-500/20"
            }`}
            title="Click to configure Backend Engine connection"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendStatus === "connected"
                  ? "bg-emerald-400 animate-pulse"
                  : backendStatus === "checking"
                  ? "bg-amber-400 animate-spin"
                  : "bg-red-400"
              }`}
            />
            <span>
              {backendStatus === "connected"
                ? `Engine: Ready (${engineInfo?.device?.toUpperCase() || "CPU"})`
                : backendStatus === "checking"
                ? "Engine: Connecting..."
                : "Engine: Disconnected"}
            </span>
            <Settings className="w-3.5 h-3.5 ml-0.5 opacity-60" />
          </button>

          <div className="flex items-center gap-2 text-xs bg-indigo-500/10 text-indigo-400 px-3 py-1.5 rounded-full border border-indigo-500/20">
            <ShieldCheck className="w-3.5 h-3.5" />
            Antigravity Bridge: Active
          </div>
        </div>
      </header>

      {/* Cloud Environment Warning Banner (if running on Vercel without local connection) */}
      {isVercelEnv && backendStatus !== "connected" && (
        <div className="bg-gradient-to-r from-amber-500/15 via-indigo-500/10 to-pink-500/15 border-b border-amber-500/20 px-6 py-2.5 text-xs text-amber-200 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Running on Vercel Cloud:</strong> AutoClip Pro's AI pipeline (FFmpeg, faster-whisper, OpenCV) runs locally on your machine.
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <a
              href="http://localhost:3000"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 font-semibold border border-amber-500/30 flex items-center gap-1 transition"
            >
              Open Local Dashboard (http://localhost:3000)
              <ExternalLink className="w-3 h-3" />
            </a>
            <button
              onClick={() => setShowSettingsModal(true)}
              className="px-3 py-1 rounded-lg bg-[#1E2235] hover:bg-[#282D45] text-gray-300 font-medium transition"
            >
              Configure Tunnel
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8 space-y-10">
        {/* Hero & Ingestion Zone */}
        <section className="text-center space-y-4 max-w-3xl mx-auto pt-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-r from-indigo-500/10 to-pink-500/10 border border-indigo-500/20 text-xs text-indigo-300">
            <TrendingUp className="w-3.5 h-3.5 text-pink-400" />
            Autonomous Highlight Extraction + Gaming Split-Screen + Hormozi Captions
          </div>
          <h1 className="text-4xl sm:text-5xl font-black tracking-tight leading-tight">
            Turn YouTube Streams into <br />
            <span className="bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-500 bg-clip-text text-transparent">
              Viral YouTube Shorts
            </span>
          </h1>
          <p className="text-gray-400 text-sm sm:text-base">
            Provide any YouTube video or live stream link. Our AI tracks streamer facecams, crops gameplay, burns animated subtitles, ranks virality rate, and autonomously posts via Antigravity.
          </p>

          {/* URL Input Box */}
          <div className="pt-2">
            <div className="relative flex items-center bg-[#12141D] rounded-2xl border border-[#232738] p-2 shadow-2xl focus-within:border-indigo-500 transition-all">
              <Youtube className="w-6 h-6 text-red-500 ml-3 shrink-0" />
              <input
                type="text"
                placeholder="Paste YouTube Video or Live Stream URL (e.g. https://www.youtube.com/watch?v=...)"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full bg-transparent px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none"
              />
              <button
                onClick={fetchVideoInfo}
                disabled={isFetchingInfo || !url.trim()}
                className="px-5 py-2.5 rounded-xl bg-[#1E2235] hover:bg-[#282D45] text-xs font-semibold text-gray-200 transition flex items-center gap-2 whitespace-nowrap disabled:opacity-50"
              >
                {isFetchingInfo ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : "Preview"}
              </button>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-300 text-xs flex flex-col sm:flex-row items-center gap-3 text-left">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
              <div className="flex-1 leading-relaxed">
                <strong>Error:</strong> {error}
              </div>
              {backendStatus === "disconnected" && (
                <button
                  onClick={() => setShowSettingsModal(true)}
                  className="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-200 font-semibold text-[11px] whitespace-nowrap transition border border-red-500/30"
                >
                  Configure Engine
                </button>
              )}
            </div>
          )}
        </section>

        {/* Video Info Preview (if loaded) */}
        {videoInfo && (
          <div className="bg-[#12141D] rounded-2xl border border-[#232738] p-4 flex flex-col sm:flex-row items-center gap-4">
            <img 
              src={videoInfo.thumbnail} 
              alt={videoInfo.title}
              className="w-44 h-24 object-cover rounded-xl border border-gray-800"
            />
            <div className="flex-1 text-left">
              <div className="flex items-center gap-2 mb-1">
                {videoInfo.is_live && (
                  <span className="px-2 py-0.5 text-[10px] font-bold bg-red-600 text-white rounded uppercase animate-pulse">
                    LIVE NOW
                  </span>
                )}
                {videoInfo.was_live && (
                  <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-600/80 text-white rounded uppercase">
                    STREAM VOD
                  </span>
                )}
                <span className="text-xs text-indigo-400 font-medium">Channel: {videoInfo.uploader}</span>
              </div>
              <h3 className="font-bold text-sm text-gray-100 line-clamp-1">{videoInfo.title}</h3>
              <p className="text-xs text-gray-500 mt-1">Duration: {Math.floor(videoInfo.duration / 60)}m {videoInfo.duration % 60}s</p>
            </div>
          </div>
        )}

        {/* Configuration Bar */}
        <section className="bg-[#12141D] rounded-2xl border border-[#232738] p-6 space-y-6">
          <h2 className="text-base font-bold text-gray-200 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            Clipping Controls & Customization
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Target Duration */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-gray-400 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                Target Clip Length
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[15, 30, 60].map((dur) => (
                  <button
                    key={dur}
                    onClick={() => setTargetDuration(dur)}
                    className={`py-2 rounded-xl text-xs font-bold transition border ${
                      targetDuration === dur 
                        ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30" 
                        : "bg-[#1A1D2B] text-gray-400 border-transparent hover:border-gray-700"
                    }`}
                  >
                    {dur}s
                  </button>
                ))}
              </div>
            </div>

            {/* Layout Mode */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-gray-400 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
                Layout & Framing
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setSplitScreen(true)}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition border text-left flex items-center gap-2 ${
                    splitScreen 
                      ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30" 
                      : "bg-[#1A1D2B] text-gray-400 border-transparent hover:border-gray-700"
                  }`}
                >
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  Split (Cam+Game)
                </button>
                <button
                  onClick={() => setSplitScreen(false)}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition border text-left flex items-center gap-2 ${
                    !splitScreen 
                      ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30" 
                      : "bg-[#1A1D2B] text-gray-400 border-transparent hover:border-gray-700"
                  }`}
                >
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-400" />
                  Center 9:16
                </button>
              </div>
            </div>

            {/* Number of Clips */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-gray-400 flex items-center justify-between">
                <span>Number of Viral Clips</span>
                <span className="text-indigo-400 font-bold">{maxClips} clips</span>
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={maxClips}
                onChange={(e) => setMaxClips(Number(e.target.value))}
                className="w-full accent-indigo-500 bg-[#1A1D2B] h-2 rounded-lg cursor-pointer"
              />
            </div>
          </div>

          {/* On-Video Text & Watermark Options */}
          <div className="pt-4 border-t border-[#1E2235] space-y-3">
            <label className="text-xs font-semibold text-gray-300 flex items-center justify-between">
              <span>On-Video Text & Overlay Controls</span>
              <span className="text-[11px] text-gray-500">Toggle text overlays on or off</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Attribution Watermark toggle */}
              <button
                type="button"
                onClick={() => setShowWatermark(!showWatermark)}
                className={`p-3 rounded-xl border text-left flex items-start gap-2.5 transition ${
                  showWatermark
                    ? "bg-indigo-600/20 border-indigo-500/50 text-white"
                    : "bg-[#1A1D2B] border-transparent hover:border-gray-700 text-gray-400"
                }`}
              >
                <input
                  type="checkbox"
                  checked={showWatermark}
                  onChange={() => {}}
                  className="mt-0.5 accent-indigo-500 rounded cursor-pointer"
                />
                <div>
                  <p className="text-xs font-bold text-gray-200">Attribution Watermark</p>
                  <p className="text-[10px] text-gray-400">"Clip from @Streamer" (Disabled by default)</p>
                </div>
              </button>

              {/* Middle Headline Banner toggle */}
              <button
                type="button"
                onClick={() => setShowHeadline(!showHeadline)}
                className={`p-3 rounded-xl border text-left flex items-start gap-2.5 transition ${
                  showHeadline
                    ? "bg-indigo-600/20 border-indigo-500/50 text-white"
                    : "bg-[#1A1D2B] border-transparent hover:border-gray-700 text-gray-400"
                }`}
              >
                <input
                  type="checkbox"
                  checked={showHeadline}
                  onChange={() => {}}
                  className="mt-0.5 accent-indigo-500 rounded cursor-pointer"
                />
                <div>
                  <p className="text-xs font-bold text-gray-200">Center Viral Hook</p>
                  <p className="text-[10px] text-gray-400">Middle divider hook headline</p>
                </div>
              </button>

              {/* Dynamic Captions toggle */}
              <button
                type="button"
                onClick={() => setShowCaptions(!showCaptions)}
                className={`p-3 rounded-xl border text-left flex items-start gap-2.5 transition ${
                  showCaptions
                    ? "bg-indigo-600/20 border-indigo-500/50 text-white"
                    : "bg-[#1A1D2B] border-transparent hover:border-gray-700 text-gray-400"
                }`}
              >
                <input
                  type="checkbox"
                  checked={showCaptions}
                  onChange={() => {}}
                  className="mt-0.5 accent-indigo-500 rounded cursor-pointer"
                />
                <div>
                  <p className="text-xs font-bold text-gray-200">Animated Captions</p>
                  <p className="text-[10px] text-gray-400">Hormozi karaoke subtitles</p>
                </div>
              </button>
            </div>
          </div>

          {/* AI Features Checklist */}
          <div className="pt-2 border-t border-[#1E2235] grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] text-gray-400">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Dynamic Hormozi Captions
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Chat Replay Velocity Tracking
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Content ID Copyright Shield
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Autonomous Antigravity Post
            </div>
          </div>

          {/* Start CTA */}
          <button
            onClick={startClipping}
            disabled={isProcessing || !url.trim()}
            className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-extrabold text-sm shadow-xl shadow-indigo-600/25 flex items-center justify-center gap-2 transition disabled:opacity-50"
          >
            {isProcessing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Processing Stream... {progressStep}
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-yellow-300" />
                Generate Viral Shorts Now
              </>
            )}
          </button>
        </section>

        {/* Results Gallery */}
        {clips.length > 0 && (
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-black text-gray-100 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-pink-500" />
                Generated Viral Shorts ({clips.length})
              </h2>
              <span className="text-xs text-gray-400">Sorted by Virality Potential</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {clips.map((clip) => (
                <div 
                  key={clip.clip_id}
                  className="bg-[#12141D] rounded-2xl border border-[#232738] overflow-hidden flex flex-col hover:border-indigo-500/50 transition-all shadow-xl"
                >
                  {/* Preview Mode Switcher Tabs */}
                  <div className="flex items-center justify-between bg-[#161822] px-3 py-2 border-b border-[#232738] text-[11px]">
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => setPreviewModes(prev => ({ ...prev, [clip.clip_id]: "video" }))}
                        className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                          (previewModes[clip.clip_id] || "video") === "video"
                            ? "bg-indigo-600 text-white shadow"
                            : "text-gray-400 hover:text-gray-200"
                        }`}
                      >
                        <Play className="w-3 h-3" /> Video
                      </button>
                      <button
                        onClick={() => setPreviewModes(prev => ({ ...prev, [clip.clip_id]: "thumb_vert" }))}
                        className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                          previewModes[clip.clip_id] === "thumb_vert"
                            ? "bg-indigo-600 text-white shadow"
                            : "text-gray-400 hover:text-gray-200"
                        }`}
                      >
                        <ImageIcon className="w-3 h-3" /> 9:16 Cover
                      </button>
                      <button
                        onClick={() => setPreviewModes(prev => ({ ...prev, [clip.clip_id]: "thumb_land" }))}
                        className={`px-2.5 py-1 rounded-lg font-bold transition flex items-center gap-1 ${
                          previewModes[clip.clip_id] === "thumb_land"
                            ? "bg-indigo-600 text-white shadow"
                            : "text-gray-400 hover:text-gray-200"
                        }`}
                      >
                        <Layers className="w-3 h-3" /> 16:9 Thumb
                      </button>
                    </div>
                    <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      1080p
                    </span>
                  </div>

                  {/* Video / Thumbnail Display Container */}
                  <div className="relative aspect-[9/16] bg-black max-h-[460px] flex items-center justify-center overflow-hidden">
                    {(previewModes[clip.clip_id] || "video") === "video" && (
                      <video
                        src={`${videoBaseUrl}${clip.relative_video_path}`}
                        controls
                        className="w-full h-full object-cover"
                      />
                    )}

                    {previewModes[clip.clip_id] === "thumb_vert" && (
                      <img
                        src={
                          clip.thumbnails?.vertical
                            ? `${videoBaseUrl}${clip.thumbnails.vertical}`
                            : `${videoBaseUrl}${clip.relative_video_path.replace('.mp4', '_thumb_vertical.jpg')}`
                        }
                        alt="9:16 Shorts Cover"
                        className="w-full h-full object-cover"
                      />
                    )}

                    {previewModes[clip.clip_id] === "thumb_land" && (
                      <div className="w-full h-full flex flex-col items-center justify-center bg-black p-3 text-center">
                        <img
                          src={
                            clip.thumbnails?.landscape
                              ? `${videoBaseUrl}${clip.thumbnails.landscape}`
                              : `${videoBaseUrl}${clip.relative_video_path.replace('.mp4', '_thumb_landscape.jpg')}`
                          }
                          alt="16:9 YouTube Thumbnail"
                          className="w-full aspect-[16/9] object-contain rounded-lg border border-gray-800 shadow-2xl"
                        />
                        <span className="text-[11px] text-gray-400 mt-3 font-semibold">
                          1280x720 High-CTR YouTube Thumbnail
                        </span>
                      </div>
                    )}
                    
                    {/* Virality Score Badge */}
                    <div className="absolute top-3 right-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-pink-500/30 flex items-center gap-1.5 shadow-lg z-10">
                      <Sparkles className="w-3.5 h-3.5 text-pink-400" />
                      <span className="font-black text-xs text-pink-300">
                        {clip.virality_rate}/100
                      </span>
                    </div>

                    <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-md px-2.5 py-1 rounded-md text-[10px] font-bold text-gray-300 z-10">
                      Clip #{clip.clip_index} • {Math.round(clip.duration)}s
                    </div>
                  </div>

                  {/* Metadata & Actions */}
                  <div className="p-4 flex-1 flex flex-col justify-between space-y-4">
                    <div>
                      <h4 className="font-bold text-sm text-gray-100 line-clamp-2">
                        {clip.title}
                      </h4>
                      <p className="text-xs text-gray-400 line-clamp-2 mt-1 italic">
                        "{clip.text}"
                      </p>

                      {/* Virality Breakdown */}
                      <div className="mt-3 pt-3 border-t border-[#1E2235] grid grid-cols-2 gap-2 text-[10px]">
                        <div className="flex justify-between text-gray-400">
                          <span>Hook:</span>
                          <span className="text-emerald-400 font-bold">{clip.virality_breakdown.hook_strength}%</span>
                        </div>
                        <div className="flex justify-between text-gray-400">
                          <span>Emotion:</span>
                          <span className="text-indigo-400 font-bold">{clip.virality_breakdown.emotional_intensity}%</span>
                        </div>
                        <div className="flex justify-between text-gray-400">
                          <span>Story Flow:</span>
                          <span className="text-purple-400 font-bold">{clip.virality_breakdown.narrative_flow}%</span>
                        </div>
                        <div className="flex justify-between text-gray-400">
                          <span>Loop Score:</span>
                          <span className="text-pink-400 font-bold">{clip.virality_breakdown.rewatchability}%</span>
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons & Thumbnail Downloads */}
                    <div className="pt-2 space-y-2">
                      <div className="grid grid-cols-2 gap-2">
                        <a
                          href={
                            clip.thumbnails?.vertical
                              ? `${videoBaseUrl}${clip.thumbnails.vertical}`
                              : `${videoBaseUrl}${clip.relative_video_path.replace('.mp4', '_thumb_vertical.jpg')}`
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                          download={`cover_${clip.clip_id}.jpg`}
                          className="py-2 px-2.5 rounded-xl bg-[#1A1D2B] hover:bg-[#23273A] border border-[#2B3048] text-[11px] font-semibold text-gray-300 flex items-center justify-center gap-1.5 transition"
                        >
                          <Download className="w-3.5 h-3.5 text-indigo-400" />
                          9:16 Cover
                        </a>

                        <a
                          href={
                            clip.thumbnails?.landscape
                              ? `${videoBaseUrl}${clip.thumbnails.landscape}`
                              : `${videoBaseUrl}${clip.relative_video_path.replace('.mp4', '_thumb_landscape.jpg')}`
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                          download={`thumbnail_${clip.clip_id}.jpg`}
                          className="py-2 px-2.5 rounded-xl bg-[#1A1D2B] hover:bg-[#23273A] border border-[#2B3048] text-[11px] font-semibold text-gray-300 flex items-center justify-center gap-1.5 transition"
                        >
                          <ImageIcon className="w-3.5 h-3.5 text-pink-400" />
                          16:9 Thumb
                        </a>
                      </div>

                      <button
                        onClick={() => setActivePostModal(clip)}
                        className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-xs font-bold text-white flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20"
                      >
                        <UploadCloud className="w-3.5 h-3.5" />
                        Post via Antigravity
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Antigravity Autonomous Posting Modal */}
        {activePostModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[#12141D] border border-[#232738] rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-[#1E2235] pb-3">
                <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
                  <ShieldCheck className="w-5 h-5" />
                  Antigravity Autonomous YouTube Studio Upload
                </div>
                <button 
                  onClick={() => setActivePostModal(null)}
                  className="text-gray-400 hover:text-white text-xs"
                >
                  ✕
                </button>
              </div>

              {/* Thumbnail & Video Summary Banner */}
              <div className="flex gap-4 items-center bg-[#1A1D2B] p-3 rounded-xl border border-[#2B3048]">
                <img
                  src={
                    activePostModal.thumbnails?.vertical
                      ? `${videoBaseUrl}${activePostModal.thumbnails.vertical}`
                      : `${videoBaseUrl}${activePostModal.relative_video_path.replace('.mp4', '_thumb_vertical.jpg')}`
                  }
                  alt="Thumbnail"
                  className="w-16 h-28 object-cover rounded-lg border border-gray-700 shrink-0"
                />
                <div className="text-[11px] text-gray-300 space-y-1">
                  <p className="font-bold text-white text-xs">Ready for Autonomous Upload</p>
                  <p className="text-gray-400">Antigravity will upload this 1080p Short and apply the generated high-CTR cover.</p>
                  <span className="inline-block px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-bold">1080x1920 Full HD</span>
                </div>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="text-gray-400 block mb-1 font-semibold">Video Title (Curiosity Hook)</label>
                  <input
                    type="text"
                    defaultValue={activePostModal.title}
                    className="w-full bg-[#1A1D2B] border border-[#2B3048] rounded-xl p-2.5 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-gray-400 block mb-1 font-semibold">SEO Description & Attribution</label>
                  <textarea
                    rows={4}
                    defaultValue={activePostModal.description}
                    className="w-full bg-[#1A1D2B] border border-[#2B3048] rounded-xl p-2.5 text-white text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-[11px] text-indigo-300 space-y-1">
                  <p className="font-bold">⚡ How Antigravity Will Post This:</p>
                  <p>1. Connects with your local Google Chrome session via Chrome DevTools MCP.</p>
                  <p>2. Automates YouTube Studio upload dialog directly (bypassing the 6 uploads/day API quota).</p>
                  <p>3. Uploads binary, sets title, description, tags, and audience without manual intervention.</p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  onClick={() => setActivePostModal(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-400 hover:bg-[#1A1D2B]"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleAntigravityUpload(activePostModal)}
                  disabled={antigravityPosting}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-xs font-bold text-white flex items-center gap-2"
                >
                  {antigravityPosting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <UploadCloud className="w-3.5 h-3.5" />}
                  Confirm & Post to YouTube
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Engine Configuration Modal */}
        {showSettingsModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[#12141D] border border-[#232738] rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-[#1E2235] pb-3">
                <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
                  <Server className="w-5 h-5" />
                  AutoClip Engine Connection
                </div>
                <button 
                  onClick={() => setShowSettingsModal(false)}
                  className="text-gray-400 hover:text-white text-xs"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <label className="text-gray-300 block mb-1 font-semibold">Backend Engine URL</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={customInputUrl}
                      onChange={(e) => setCustomInputUrl(e.target.value)}
                      placeholder="e.g. http://localhost:8000 or https://xyz.ngrok-free.app"
                      className="flex-1 bg-[#1A1D2B] border border-[#2B3048] rounded-xl px-3 py-2 text-white text-xs focus:outline-none focus:border-indigo-500"
                    />
                    <button
                      onClick={() => checkHealth(customInputUrl)}
                      disabled={isCheckingHealth}
                      className="px-3 py-2 rounded-xl bg-[#1E2235] hover:bg-[#282D45] text-xs font-semibold text-gray-200 transition shrink-0"
                    >
                      {isCheckingHealth ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : "Test"}
                    </button>
                  </div>
                </div>

                {/* Connection Status Indicator */}
                <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${
                  backendStatus === "connected"
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                    : "bg-red-500/10 border-red-500/20 text-red-300"
                }`}>
                  {backendStatus === "connected" ? (
                    <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                  )}
                  <div>
                    <span className="font-bold">
                      {backendStatus === "connected" ? "Engine Connected & Operational" : "Engine Unreachable"}
                    </span>
                    {backendStatus === "connected" && engineInfo && (
                      <p className="text-[11px] text-emerald-400/80 mt-0.5">
                        Compute: {engineInfo.device?.toUpperCase()} • Whisper: {engineInfo.whisper_model}
                      </p>
                    )}
                  </div>
                </div>

                {/* Quick Presets */}
                <div className="space-y-1.5">
                  <span className="text-gray-400 text-[11px] font-medium">Quick Presets:</span>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => setCustomInputUrl("http://localhost:8000")}
                      className="px-2.5 py-1 rounded-lg bg-[#1A1D2B] hover:bg-[#252A3E] text-[11px] text-gray-300 border border-gray-700/50"
                    >
                      Localhost (http://localhost:8000)
                    </button>
                    <button
                      onClick={() => setCustomInputUrl("")}
                      className="px-2.5 py-1 rounded-lg bg-[#1A1D2B] hover:bg-[#252A3E] text-[11px] text-gray-300 border border-gray-700/50"
                    >
                      Proxy Default (/api/backend)
                    </button>
                  </div>
                </div>

                {/* Explanation */}
                <div className="p-3 bg-[#161926] border border-[#232738] rounded-xl text-[11px] text-gray-400 space-y-1.5 leading-relaxed">
                  <p className="font-semibold text-gray-200">💡 Why is this needed?</p>
                  <p>
                    AutoClip Pro renders heavy 1080×1920 60FPS split-screen videos and runs AI speech models using your computer's CPU/GPU and FFmpeg.
                  </p>
                  {isVercelEnv && (
                    <p className="text-amber-300/90">
                      When viewing on <strong>Vercel</strong>, web browsers block cloud-to-localhost connections. For optimal performance, run AutoClip Pro locally at <strong>http://localhost:3000</strong> using <code className="bg-black/50 px-1 py-0.5 rounded text-amber-200">start_frontend.bat</code>.
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2 border-t border-[#1E2235]">
                <button
                  onClick={() => setShowSettingsModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-400 hover:bg-[#1A1D2B]"
                >
                  Close
                </button>
                <button
                  onClick={handleSaveSettings}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-xs font-bold text-white shadow-lg shadow-indigo-600/20"
                >
                  Save & Connect
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1E2235] py-6 text-center text-xs text-gray-500 bg-[#090A0F]">
        AutoClip Pro • Powered by Antigravity, faster-whisper, MediaPipe & FFmpeg • Ready for Vercel & Local Deployment
      </footer>
    </div>
  );
}