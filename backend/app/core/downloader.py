import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import yt_dlp
from backend.app.config import DOWNLOADS_DIR, TEMP_DIR

class VideoDownloader:
    def __init__(self, output_dir: Path = DOWNLOADS_DIR):
        self.output_dir = output_dir

    def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract metadata without downloading."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'js_runtimes': {'node': {}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "id": info.get("id"),
                "title": info.get("title"),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader"),
                "description": info.get("description", ""),
                "thumbnail": info.get("thumbnail"),
                "is_live": info.get("is_live", False),
                "was_live": info.get("was_live", False)
            }

    def download_video(
        self,
        url: str,
        start_offset_seconds: int = 600,
        window_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Downloads high-quality 1080p stream slice and extracts 16kHz mono audio.
        Supports offset scanning so subsequent runs process fresh parts of the stream.
        """
        info = self.extract_info(url)
        video_id = info["id"]
        duration = info.get("duration", 0)
        
        # Unique file tag based on offset so multiple runs don't overwrite each other
        file_tag = f"{video_id}_sec{start_offset_seconds}"
        video_path = self.output_dir / f"{file_tag}.mp4"
        audio_path = self.output_dir / f"{file_tag}_audio.wav"
        chat_path = self.output_dir / f"{video_id}_chat.json"

        # Download high quality 1080p 60fps using resilient HLS/MP4 formats
        ydl_opts = {
            'js_runtimes': {'node': {}},
            'format': '617+140/303+140/bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'outtmpl': str(self.output_dir / f"{file_tag}.%(ext)s"),
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': True,
        }


        if duration > window_minutes * 60:
            start_sec = min(start_offset_seconds, max(0, int(duration - (window_minutes * 60))))
            end_sec = start_sec + (window_minutes * 60)
            ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func(None, [(start_sec, end_sec)])
            ydl_opts['force_keyframes_at_cuts'] = True
            print(f"[Downloader] 1080p High-Quality Stream Ingestion: Window {start_sec}s -> {end_sec}s (~{window_minutes} mins)...")

        if not video_path.exists():
            print(f"[Downloader] Downloading 1080p video from: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # Extract 16kHz mono WAV for fast Whisper transcription
        if not audio_path.exists():
            print(f"[Downloader] Extracting 16kHz audio track...")
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vn",
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                str(audio_path)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if info.get("is_live") or info.get("was_live"):
            self._try_download_chat(url, chat_path)

        return {
            "info": info,
            "video_path": str(video_path),
            "audio_path": str(audio_path),
            "chat_path": str(chat_path) if chat_path.exists() else None,
            "window_start": start_sec if duration > window_minutes * 60 else 0
        }


    def _try_download_chat(self, url: str, output_chat_path: Path):
        """Attempts to download live chat replay via chat_downloader."""
        if output_chat_path.exists():
            return
        try:
            print("[Downloader] Attempting live chat replay download...")
            from chat_downloader import ChatDownloader
            downloader = ChatDownloader()
            chat = downloader.get_chat(url, max_messages=10000)
            messages = []
            for item in chat:
                messages.append({
                    "time_in_seconds": item.get("time_in_seconds", 0),
                    "author": item.get("author", {}).get("name", "anon"),
                    "message": item.get("message", "")
                })
            with open(output_chat_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2)
            print(f"[Downloader] Chat replay saved with {len(messages)} messages.")
        except Exception as e:
            print(f"[Downloader] Chat replay not available or skipped: {e}")
