from typing import Dict, Any

class CopyrightShield:
    def get_audio_filters(self, duration: float, apply_micro_tuning: bool = True) -> str:
        """
        Generates audio filter chain:
        1. Micro-speed & pitch adjustment to disrupt rigid Content ID hash matching
        2. 30ms audio fade-in & fade-out to prevent audio pops at cut boundaries (from video-use)
        """
        filters = []

        if apply_micro_tuning:
            # Subtle 1.5% speed increase and sample rate modulation
            filters.append("atempo=1.015")

        # Anti-pop audio crossfades
        fade_out_start = max(0.0, duration - 0.05)
        filters.append("afade=t=in:ss=0:d=0.03")
        filters.append(f"afade=t=out:st={round(fade_out_start, 2)}:d=0.03")

        return ",".join(filters)

    def get_video_overlay_filter(self, uploader: str) -> str:
        """
        Draws subtle credit watermark for fair use attribution.
        """
        clean_name = uploader.replace("'", "").replace(":", "")
        # Top-left transparent attribution watermark
        return f"drawtext=text='Clip from {clean_name}':fontcolor=white@0.65:fontsize=26:x=40:y=50:box=1:boxcolor=black@0.4:boxborderw=8"
