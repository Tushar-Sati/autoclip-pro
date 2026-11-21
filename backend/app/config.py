import os
import sys
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
DOWNLOADS_DIR = STORAGE_DIR / "downloads"
CLIPS_DIR = STORAGE_DIR / "clips"
TEMP_DIR = STORAGE_DIR / "temp"

for d in [DOWNLOADS_DIR, CLIPS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Auto-detect FFmpeg binary path on Windows
local_appdata = os.environ.get("LOCALAPPDATA", "")
if local_appdata:
    winget_packages = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
    if winget_packages.exists():
        found_ffmpeg = list(winget_packages.glob("**/bin/ffmpeg.exe"))
        if found_ffmpeg:
            ffmpeg_bin = str(found_ffmpeg[0].parent)
            if ffmpeg_bin not in os.environ.get("PATH", ""):
                os.environ["PATH"] = ffmpeg_bin + os.pathsep + os.environ.get("PATH", "")

# Configure Fontconfig for Windows FFmpeg libass & drawtext support
fonts_conf = TEMP_DIR / "fonts.conf"
if not fonts_conf.exists():
    fonts_conf.write_text(
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n'
        '<fontconfig>\n'
        '  <dir>C:\\Windows\\Fonts</dir>\n'
        '  <config></config>\n'
        '</fontconfig>\n',
        encoding="utf-8"
    )
os.environ["FONTCONFIG_FILE"] = str(fonts_conf)


class Settings(BaseModel):
    app_name: str = "AutoClip Pro"
    version: str = "1.0.0"
    target_width: int = 1080
    target_height: int = 1920
    default_clip_duration: int = 30 # seconds
    min_clip_duration: int = 15
    max_clip_duration: int = 90
    whisper_model_size: str = "small" # base, small, medium
    device: str = "cpu" # "cuda" or "cpu"
    compute_type: str = "int8" # "float16" for GPU, "int8" for CPU

settings = Settings()

