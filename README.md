# 🚀 AutoClip Pro - Autonomous AI YouTube Video & Stream Clipper

AutoClip Pro is a state-of-the-art, fully automated clipping and YouTube Shorts generator designed for content creators, streamers, and clipping channels. 

Given any **YouTube video URL** or **YouTube Live Stream link**, AutoClip Pro autonomously analyzes the footage, identifies peak viral moments, tracks the streamer's facecam, stacks the gameplay and facecam into a **9:16 split-screen layout**, generates **dynamic Hormozi-style animated captions**, scores **virality rate (0–100)**, generates curiosity-gap titles/descriptions/hashtags, and coordinates with **Antigravity** to autonomously upload directly to **YouTube Studio**.

---

## 🌟 Key Features

1. **YouTube Video & Live Stream Ingestion:**
   * Seamlessly downloads videos or live streams using `yt-dlp`.
   * For concluded streams or live broadcasts, it downloads the live chat replay to perform audience message-rate spike analysis.
2. **Customizable Clip Duration:**
   * Choose target clip lengths: **15s, 30s, 60s**, or custom duration ranges.
3. **Multi-Signal Viral Moment Extraction:**
   * **Chat Velocity Spikes:** Flags moments where audience activity exceeds $\mu + 2.5\sigma$ and triggers hype emotes (`POG`, `LMAO`, `W`, `HOLY`, `WTF`).
   * **Acoustic Loudness & Energy:** Catches screams, laughter, dramatic gasps.
   * **LLM Hook Scorer:** Evaluates the opening 3–5 seconds and narrative coherence.
4. **Smart Split-Screen Framing (Facecam + Gameplay):**
   * Uses computer vision (**MediaPipe / OpenCV**) to detect the streamer's webcam box in any quadrant.
   * Clusters face detections to lock the webcam frame without camera jitter.
   * Scales the streamer cam into the top 1080×960 and centers the gameplay in the bottom 1080×960.
5. **Dynamic Animated Karaoke Captions:**
   * Generates Advanced SubStation Alpha (`.ass`) subtitles styled like Alex Hormozi and TikTok shorts.
   * Spoken words bounce with neon yellow highlights while the rest of the phrase stays crisp white with heavy black outlines.
6. **Copyright & Content ID Defense Shield:**
   * Audio micro-tuning (+1.5% speed, subtle pitch offset) to disrupt static Content ID acoustic fingerprint matching.
   * 30ms anti-pop audio crossfades at cut boundaries (inspired by `browser-use/video-use`).
   * Sleek attribution watermark burned into top-left (`Clip from @Streamer`) to solidify Transformative Fair Use.
7. **Antigravity Autonomous Chrome DevTools Uploader:**
   * Bypasses the strict YouTube Data API v3 daily upload limit (which caps channels at only 6 uploads/day).
   * Antigravity operates Google Chrome directly via Chrome DevTools MCP: uploads the video binary, enters the viral title, description, and hashtags, sets "Not made for kids", and publishes automatically.

---

## 📁 Project Architecture

```
cliping tool/
├── backend/
│   ├── app/
│   │   ├── config.py                   # Auto-detects FFmpeg & Fontconfig on Windows
│   │   ├── main.py                     # FastAPI application endpoints
│   │   ├── core/
│   │   │   ├── downloader.py           # yt-dlp video & live chat downloader
│   │   │   ├── transcriber.py          # faster-whisper word-level transcription
│   │   │   ├── facecam_detector.py     # OpenCV/MediaPipe facecam locator & 9:16 layout
│   │   │   ├── highlight_detector.py   # Chat spikes + hook density detector
│   │   │   ├── subtitle_generator.py   # Hormozi animated ASS subtitle creator
│   │   │   ├── virality_scorer.py      # 0-100 virality rating & title/tag generator
│   │   │   ├── copyright_shield.py     # Audio micro-tuning & attribution filters
│   │   │   ├── video_renderer.py       # FFmpeg split-screen & subtitle composite
│   │   │   └── pipeline.py             # Master orchestrator
│   │   └── automation/
│   │       └── youtube_uploader.py     # Chrome DevTools / Antigravity posting plan
│   ├── requirements.txt
│   └── run_server.py
├── frontend/                           # Next.js 14 + Tailwind CSS (Ready for Vercel)
│   ├── src/app/page.tsx                # Interactive modern dashboard
│   ├── vercel.json                     # Vercel deployment configuration
│   └── package.json
├── storage/
│   ├── downloads/                      # Raw downloaded video & audio streams
│   ├── clips/                          # Rendered 9:16 vertical shorts & summaries
│   └── temp/                           # Intermediate ASS subtitles & wav tracks
├── start_backend.bat                   # 1-Click backend launcher
├── start_frontend.bat                  # 1-Click frontend launcher
├── test_pipeline.py                    # Diagnostic verification script
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Launch the Backend Engine
Double-click `start_backend.bat` or run in terminal:
```powershell
backend\venv\Scripts\activate.bat
python backend\run_server.py
```
* Backend API: `http://localhost:8000`
* Interactive API Documentation: `http://localhost:8000/docs`

### 2. Launch the Next.js Frontend
Double-click `start_frontend.bat` or run:
```powershell
cd frontend
npm run dev
```
* Open your browser at: `http://localhost:3000`

### 3. Deploy Frontend to Vercel
1. Push this repository to GitHub.
2. In [Vercel](https://vercel.com), click **Add New Project** and select the repository.
3. Set the Root Directory to `frontend`.
4. Click **Deploy**. Vercel will build and host your frontend globally.

---

## 🤖 Antigravity Autonomous YouTube Studio Posting

When you review your generated clips in the dashboard:
1. Click **"Post via Antigravity"** on any Short.
2. Review the curiosity-gap title, description, and tags.
3. Click **"Confirm & Post to YouTube"**.
4. Antigravity connects to your authenticated Chrome browser session via **Chrome DevTools MCP**, navigates to YouTube Studio, drags and drops the Short `.mp4`, fills out all viral metadata, and clicks Publish autonomously!
