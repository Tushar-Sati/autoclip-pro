import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.config import CLIPS_DIR, TEMP_DIR
from backend.app.core.downloader import VideoDownloader
from backend.app.core.transcriber import AudioTranscriber
from backend.app.core.facecam_detector import FacecamDetector
from backend.app.core.highlight_detector import HighlightDetector
from backend.app.core.subtitle_generator import SubtitleGenerator
from backend.app.core.virality_scorer import ViralityScorer
from backend.app.core.video_renderer import VideoRenderer

class ClippingPipeline:
    def __init__(self):
        self.downloader = VideoDownloader()
        self.transcriber = AudioTranscriber()
        self.facecam_detector = FacecamDetector()
        self.subtitle_gen = SubtitleGenerator()
        self.scorer = ViralityScorer()
        self.renderer = VideoRenderer()

    def process_url(
        self,
        youtube_url: str,
        target_duration: int = 30,
        max_clips: int = 3,
        force_split_screen: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Full end-to-end autonomous clipping pipeline.
        """
        print(f"[Pipeline] Starting process for: {youtube_url} (Target duration: {target_duration}s)")

        # 1. Download Video, Audio, and Chat
        download_result = self.downloader.download_video(youtube_url)
        video_path = download_result["video_path"]
        audio_path = download_result["audio_path"]
        chat_path = download_result["chat_path"]
        video_info = download_result["info"]
        uploader = video_info.get("uploader", "Streamer")
        video_id = video_info.get("id", "video")

        # 2. Transcribe Audio (Word-level timestamps)
        transcript = self.transcriber.transcribe(audio_path)

        # 3. Detect Facecam and Gaming Layout
        framing_info = self.facecam_detector.analyze_video(video_path)
        if force_split_screen is not None:
            framing_info["mode"] = "split_screen" if force_split_screen else "center_crop"

        # 4. Highlight & Viral Moment Detection
        detector = HighlightDetector(target_duration=target_duration)
        candidate_clips = detector.find_highlights(transcript, chat_path=chat_path, max_clips=max_clips)

        print(f"[Pipeline] Found {len(candidate_clips)} viral highlight segments.")

        # 5. Process & Render Each Candidate Clip
        rendered_clips = []
        for idx, clip in enumerate(candidate_clips):
            clip_idx = idx + 1
            clip_start = clip["start"]
            clip_end = clip["end"]
            clip_text = clip["text"]

            # Filter word-level timestamps for this clip
            clip_words = [
                w for w in transcript.get("all_words", [])
                if clip_start <= w["start"] <= clip_end
            ]

            # Generate Hormozi Animated ASS Subtitles
            ass_path = str(TEMP_DIR / f"{video_id}_clip_{clip_idx}.ass")
            self.subtitle_gen.generate_ass(
                words=clip_words,
                output_path=ass_path,
                clip_start=clip_start,
                clip_duration=clip["duration"],
                vertical_margin=420,
                uploader=uploader
            )


            # Evaluate Virality Score & Generate Viral Titles/Metadata
            virality_eval = self.scorer.evaluate_clip(
                text=clip_text,
                duration=clip["duration"],
                uploader=uploader
            )

            # Render Final 9:16 Video
            output_clip_path = str(CLIPS_DIR / f"{video_id}_short_{clip_idx}.mp4")
            self.renderer.render_short(
                input_video=video_path,
                start_time=clip_start,
                end_time=clip_end,
                framing_info=framing_info,
                subtitle_ass_path=ass_path,
                output_path=output_clip_path,
                uploader=uploader
            )

            rendered_clips.append({
                "clip_id": f"{video_id}_{clip_idx}",
                "clip_index": clip_idx,
                "video_path": output_clip_path,
                "relative_video_path": f"/storage/clips/{video_id}_short_{clip_idx}.mp4",
                "start": clip_start,
                "end": clip_end,
                "duration": clip["duration"],
                "text": clip_text,
                "virality_rate": virality_eval["virality_rate"],
                "virality_breakdown": virality_eval["breakdown"],
                "title": virality_eval["selected_title"],
                "suggested_titles": virality_eval["suggested_titles"],
                "description": virality_eval["description"],
                "hashtags": virality_eval["hashtags"],
                "layout_mode": framing_info["mode"],
                "status": "ready"
            })

        result = {
            "video_info": video_info,
            "framing_info": framing_info,
            "total_clips": len(rendered_clips),
            "clips": rendered_clips
        }

        # Save summary JSON
        summary_path = CLIPS_DIR / f"{video_id}_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"[Pipeline] Pipeline complete! Output {len(rendered_clips)} shorts.")
        return result
