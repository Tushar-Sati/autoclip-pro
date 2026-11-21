import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.core.copyright_shield import CopyrightShield

class VideoRenderer:
    def __init__(self, target_width: int = 1080, target_height: int = 1920):
        self.target_width = target_width
        self.target_height = target_height
        self.half_height = target_height // 2 # 960
        self.shield = CopyrightShield()

    def render_short(
        self,
        input_video: str,
        start_time: float,
        end_time: float,
        framing_info: Dict[str, Any],
        subtitle_ass_path: Optional[str],
        output_path: str,
        uploader: str = "Streamer"
    ) -> str:
        """
        Renders the final 9:16 vertical Short with split-screen layout,
        Hormozi animated captions, and fair-use copyright protection.
        """
        duration = end_time - start_time
        mode = framing_info.get("mode", "center_crop")

        # Prepare subtitle filter if available
        sub_filter = ""
        if subtitle_ass_path and Path(subtitle_ass_path).exists():
            clean_ass = str(Path(subtitle_ass_path).resolve()).replace("\\", "/").replace(":", r"\:")
            sub_filter = f"ass='{clean_ass}'"

        audio_filters = self.shield.get_audio_filters(duration, apply_micro_tuning=True)

        if mode == "split_screen" and "facecam_box" in framing_info:
            fb = framing_info["facecam_box"]
            gb = framing_info.get("gameplay_crop", {"x": 0, "y": 0, "w": 1920, "h": 1080})

            # Top: Streamer Facecam, Bottom: Gameplay
            filter_complex = (
                f"[0:v]crop={fb['w']}:{fb['h']}:{fb['x']}:{fb['y']},"
                f"scale={self.target_width}:{self.half_height}:force_original_aspect_ratio=increase,"
                f"crop={self.target_width}:{self.half_height}[top];"
                f"[0:v]crop={gb['w']}:{gb['h']}:{gb['x']}:{gb['y']},"
                f"scale={self.target_width}:{self.half_height}:force_original_aspect_ratio=increase,"
                f"crop={self.target_width}:{self.half_height}[bottom];"
                f"[top][bottom]vstack=inputs=2"
            )

            if sub_filter:
                filter_complex += f",{sub_filter}"

            filter_complex += "[v]"

        else:
            # Center 9:16 crop
            filter_complex = (
                f"[0:v]crop=ih*9/16:ih:(iw-ow)/2:0,"
                f"scale={self.target_width}:{self.target_height}"
            )
            if sub_filter:
                filter_complex += f",{sub_filter}"
            filter_complex += "[v]"


        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-to", str(end_time),
            "-i", input_video,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "0:a?",
            "-af", audio_filters,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path)
        ]

        print(f"[VideoRenderer] Rendering clip ({start_time}s -> {end_time}s) to {output_path}...")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[VideoRenderer Error] FFmpeg failed: {res.stderr[:400]}")
            # Fallback simpler render if complex filter failed
            self._render_simple_fallback(input_video, start_time, end_time, output_path)

        print(f"[VideoRenderer] Render complete: {output_path}")
        return output_path

    def _render_simple_fallback(self, input_video: str, start_time: float, end_time: float, output_path: str):
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-to", str(end_time),
            "-i", input_video,
            "-vf", f"crop=ih*9/16:ih:(iw-ow)/2:0,scale={self.target_width}:{self.target_height}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            str(output_path)
        ]
        subprocess.run(cmd, check=True)
