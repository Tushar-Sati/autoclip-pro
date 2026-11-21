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
            'extract_flat': False
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

    def download_video(self, url: str) -> Dict[str, Any]:
        """Download video and extract 16kHz mono audio for processing."""
        info = self.extract_info(url)
        video_id = info["id"]
        video_path = self.output_dir / f"{video_id}.mp4"
        audio_path = self.output_dir / f"{video_id}_audio.wav"
        chat_path = self.output_dir / f"{video_id}_chat.json"

        # 1. Download video (max 1080p for fast processing)
        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
            'outtmpl': str(self.output_dir / f"{video_id}.%(ext)s"),
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': True,
        }

        if not video_path.exists():
            print(f"[Downloader] Downloading video: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # 2. Extract 16kHz mono WAV for fast Whisper transcription
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

        # 3. Download chat if live stream or was live
        if info.get("is_live") or info.get("was_live"):
            self._try_download_chat(url, chat_path)

        return {
            "info": info,
            "video_path": str(video_path),
            "audio_path": str(audio_path),
            "chat_path": str(chat_path) if chat_path.exists() else None
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
