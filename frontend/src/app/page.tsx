"use client";

import React, { useState } from "react";
import { 
  Play, Sparkles, Youtube, CheckCircle2, Clock, 
  Layers, Volume2, ShieldCheck, Share2, UploadCloud, 
  TrendingUp, Copy, Check, AlertCircle, RefreshCw
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
  
  // Status states
  const [isFetchingInfo, setIsFetchingInfo] = useState(false);
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressStep, setProgressStep] = useState<string>("");
  const [clips, setClips] = useState<Clip[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Modal / Antigravity posting state
  const [activePostModal, setActivePostModal] = useState<Clip | null>(null);
  const [antigravityPosting, setAntigravityPosting] = useState(false);
  const [copiedTitle, setCopiedTitle] = useState(false);

  const fetchVideoInfo = async () => {
    if (!url.trim()) return;
    setIsFetchingInfo(true);
    setError(null);
    try {
      const res = await fetch("/api/backend/info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (data.success && data.info) {
        setVideoInfo(data.info);
      } else {
        setError(data.detail || "Failed to load video information");
      }
    } catch (err: any) {
      setError("Cannot connect to backend service. Ensure local worker is running.");
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
      const res = await fetch("/api/backend/clip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          target_duration: targetDuration,
          max_clips: maxClips,
          force_split_screen: splitScreen,
        }),
      });

      const data = await res.json();
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
      const res = await fetch("/api/backend/antigravity/prepare_post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clip_id: clip.clip_id,
          title: clip.title,
          description: clip.description,
          tags: clip.hashtags,
          visibility: "public"
        })
      });
      const data = await res.json();
      if (data.success) {
        alert("🚀 Antigravity Agent Dispatched!\n\nAntigravity is now controlling Chrome & CMD to upload this Short directly to YouTube Studio without hitting API quota limits!");
        setActivePostModal(null);
      }
    } catch (err) {
      alert("Error triggering Antigravity agent.");
    } finally {
      setAntigravityPosting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090A0F] text-white flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-[#1E2235] px-6 py-4 flex items-center justify-between bg-[#12141D]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              AutoClip <span className="text-indigo-400">Pro</span>
            </span>
            <span className="text-xs ml-2 px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              v1.0 Vercel Edition
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs bg-emerald-500/10 text-emerald-400 px-3 py-1.5 rounded-full border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Local Engine: Ready
          </div>
          <div className="flex items-center gap-2 text-xs bg-indigo-500/10 text-indigo-400 px-3 py-1.5 rounded-full border border-indigo-500/20">
            <ShieldCheck className="w-3.5 h-3.5" />
            Antigravity Bridge: Active
          </div>
        </div>
      </header>

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
              <Youtube className="w-6 h-6 text-red-500 ml-3" />
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
                className="px-5 py-2.5 rounded-xl bg-[#1E2235] hover:bg-[#282D45] text-xs font-semibold text-gray-200 transition flex items-center gap-2 whitespace-nowrap"
              >
                {isFetchingInfo ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : "Preview"}
              </button>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-center gap-2 justify-center">
              <AlertCircle className="w-4 h-4" />
              {error}
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
                  {/* Video Player */}
                  <div className="relative aspect-[9/16] bg-black max-h-[460px] flex items-center justify-center overflow-hidden">
                    <video
                      src={`http://localhost:8000${clip.relative_video_path}`}
                      controls
                      className="w-full h-full object-cover"
                    />
                    
                    {/* Virality Score Badge */}
                    <div className="absolute top-3 right-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-pink-500/30 flex items-center gap-1.5 shadow-lg">
                      <Sparkles className="w-3.5 h-3.5 text-pink-400" />
                      <span className="font-black text-xs text-pink-300">
                        {clip.virality_rate}/100
                      </span>
                    </div>

                    <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-md px-2.5 py-1 rounded-md text-[10px] font-bold text-gray-300">
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

                    {/* Action Buttons */}
                    <div className="pt-2 space-y-2">
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
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1E2235] py-6 text-center text-xs text-gray-500 bg-[#090A0F]">
        AutoClip Pro • Powered by Antigravity, faster-whisper, MediaPipe & FFmpeg • Ready for Vercel Deployment
      </footer>
    </div>
  );
}
