import os
import json
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.config import settings, STORAGE_DIR, CLIPS_DIR
from backend.app.core.downloader import VideoDownloader
from backend.app.core.pipeline import ClippingPipeline

app = FastAPI(title=settings.app_name, version=settings.version)

# Enable CORS for Next.js / Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files to serve generated clips and thumbnails
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

downloader = VideoDownloader()
pipeline = ClippingPipeline()

# Job store (in-memory + disk cache)
jobs = {}

class InfoRequest(BaseModel):
    url: str

class ClipRequest(BaseModel):
    url: str
    target_duration: int = 30
    max_clips: int = 3
    force_split_screen: Optional[bool] = None

class PostRequest(BaseModel):
    clip_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: str = "public" # public, unlisted, private

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": settings.app_name,
        "version": settings.version,
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "device": settings.device,
        "whisper_model": settings.whisper_model_size,
        "clips_count": len(list(CLIPS_DIR.glob("*_summary.json")))
    }

@app.post("/api/info")
def get_video_info(req: InfoRequest):
    """Fetches video/livestream metadata without downloading."""
    try:
        info = downloader.extract_info(req.url)
        return {"success": True, "info": info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/clip")
def start_clipping(req: ClipRequest):
    """Executes the full automated clipping pipeline."""
    try:
        result = pipeline.process_url(
            youtube_url=req.url,
            target_duration=req.target_duration,
            max_clips=req.max_clips,
            force_split_screen=req.force_split_screen
        )
        return {"success": True, "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clips")
def list_clips():
    """Lists all previously generated clips with virality scores."""
    summaries = []
    for f in CLIPS_DIR.glob("*_summary.json"):
        try:
            with open(f, "r", encoding="utf-8") as sf:
                summaries.append(json.load(sf))
        except Exception:
            continue
    return {"success": True, "total_projects": len(summaries), "projects": summaries}

@app.post("/api/antigravity/prepare_post")
def prepare_antigravity_post(req: PostRequest):
    """
    Prepares payload for Antigravity's Chrome DevTools MCP or CMD
    to autonomously upload the short to YouTube Studio.
    """
    # Locate clip video
    target_video = None
    for vid in CLIPS_DIR.glob(f"*{req.clip_id}*.mp4"):
        target_video = str(vid)
        break

    if not target_video:
        # Search directly by filename
        candidates = list(CLIPS_DIR.glob(f"{req.clip_id}.mp4"))
        if candidates:
            target_video = str(candidates[0])

    if not target_video or not Path(target_video).exists():
        raise HTTPException(status_code=404, detail="Clip video file not found.")

    payload = {
        "status": "ready_for_antigravity",
        "video_path": target_video,
        "title": req.title or "Viral Moment! #Shorts",
        "description": req.description or "Automated Short #shorts",
        "tags": req.tags or ["shorts", "viral", "gaming"],
        "visibility": req.visibility,
        "instructions": "Call Antigravity's Chrome DevTools MCP or CMD uploader to publish this clip to YouTube Studio."
    }

    return {"success": True, "posting_task": payload}
