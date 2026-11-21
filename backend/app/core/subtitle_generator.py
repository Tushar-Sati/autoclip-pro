import os
from typing import List, Dict, Any, Optional
from pathlib import Path

class SubtitleGenerator:
    def __init__(self, target_width: int = 1080, target_height: int = 1920):
        self.target_width = target_width
        self.target_height = target_height

    def format_time_ass(self, seconds: float) -> str:
        """Converts float seconds to ASS timestamp format: H:MM:SS.cc"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int(round((seconds % 1) * 100))
        if centisecs >= 100:
            centisecs = 99
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def generate_ass(
        self,
        words: List[Dict[str, Any]],
        output_path: str,
        clip_start: float = 0.0,
        clip_duration: float = 30.0,
        words_per_line: int = 4,
        headline: str = "",
        highlight_color: str = "&H0000FFFF&", # Neon Yellow in ASS (BBGGRR)
        primary_color: str = "&H00FFFFFF&",   # Crisp White
        font_name: str = "Arial",
        font_size: int = 70,
        vertical_margin: int = 380,
        uploader: str = "Streamer",
        show_watermark: bool = False,
        show_headline: bool = True,
        show_captions: bool = True
    ) -> Optional[str]:
        """
        Generates an Advanced SubStation Alpha (.ass) file with optional word-by-word
        karaoke-style active highlighting, bold middle headline banner, and attribution watermark.
        """
        # If all text layers are disabled, do not generate ASS file
        if not show_watermark and not show_headline and not show_captions:
            return None

        clip_duration_str = self.format_time_ass(clip_duration)
        clean_uploader = uploader.replace("'", "").replace(":", "")
        clean_headline = headline.replace("'", "").replace(":", "").upper()

        # Header definition
        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {self.target_width}
PlayResY: {self.target_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HormoziStyle,{font_name},{font_size},{primary_color},&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,4,2,60,60,{vertical_margin},1
Style: HookHeadline,{font_name},52,&H0000FFFF&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,4,2,40,40,960,1
Style: CreditWatermark,{font_name},28,&H60FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,7,40,40,40,1
Style: SubscribeCTA,{font_name},44,&H0000FFFF&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,3,2,40,40,240,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        if show_watermark and clean_uploader:
            ass_header += f"Dialogue: 0,0:00:00.00,{clip_duration_str},CreditWatermark,,0,0,0,,Clip from @{clean_uploader}\n"

        if show_headline and clean_headline:
            ass_header += f"Dialogue: 1,0:00:00.00,{clip_duration_str},HookHeadline,,0,0,0,,{clean_headline}\n"

        dialogue_lines = []

        if not show_captions:
            # Write only headers (watermark/headline) without captions
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(ass_header)
            return output_path



        # Filter words to this clip timeframe and adjust timestamps relative to clip start
        clip_words = []
        for w in words:
            rel_start = max(0.0, w["start"] - clip_start)
            rel_end = max(rel_start + 0.1, w["end"] - clip_start)
            clip_words.append({
                "word": w["word"].upper(), # Uppercase gives high impact
                "start": rel_start,
                "end": rel_end
            })

        # Group words into small punchy phrases (chunks)
        chunks = []
        for i in range(0, len(clip_words), words_per_line):
            chunks.append(clip_words[i:i + words_per_line])

        for chunk in chunks:
            if not chunk:
                continue

            # For each word in the chunk, create a dialogue line where that specific word is highlighted
            for active_idx in range(len(chunk)):
                w_start = chunk[active_idx]["start"]
                # Active word ends when next word begins, or at chunk end
                if active_idx < len(chunk) - 1:
                    w_end = chunk[active_idx + 1]["start"]
                else:
                    w_end = chunk[-1]["end"] + 0.1

                if w_end <= w_start:
                    w_end = w_start + 0.2

                start_str = self.format_time_ass(w_start)
                end_str = self.format_time_ass(w_end)

                # Assemble line text with color overrides
                line_parts = []
                for idx, item in enumerate(chunk):
                    text = item["word"]
                    if idx == active_idx:
                        # Highlight active word with color tag and dynamic pop
                        line_parts.append(f"{{\\c{highlight_color}\\fscx115\\fscy115}}{text}{{\\r}}")
                    else:
                        line_parts.append(f"{{\\c{primary_color}}}{text}{{\\r}}")

                formatted_text = " ".join(line_parts)
                dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},HormoziStyle,,0,0,0,,{formatted_text}")

        # Add subscriber call-to-action during the final 1.8 seconds (when captions are enabled)
        if show_captions and clip_duration > 6.0:
            cta_start = self.format_time_ass(max(0.0, clip_duration - 1.8))
            dialogue_lines.append(
                f"Dialogue: 2,{cta_start},{clip_duration_str},SubscribeCTA,,0,0,0,,{{\\c&H0000FFFF&}}👉 SUBSCRIBE FOR MORE! 🔔{{\\r}}"
            )

        # Write to file with utf-8-sig encoding for ASS compatibility
        with open(output_path, "w", encoding="utf-8-sig") as f:
            f.write(ass_header + "\n".join(dialogue_lines))

        print(f"[SubtitleGenerator] Generated ASS subtitles with {len(dialogue_lines)} frames -> {output_path}")
        return output_path
