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

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.config import CLIPS_DIR, TEMP_DIR, STORAGE_DIR
from backend.app.core.downloader import VideoDownloader
from backend.app.core.transcriber import AudioTranscriber
from backend.app.core.facecam_detector import FacecamDetector
from backend.app.core.highlight_detector import HighlightDetector
from backend.app.core.subtitle_generator import SubtitleGenerator
from backend.app.core.virality_scorer import ViralityScorer
from backend.app.core.video_renderer import VideoRenderer
from backend.app.core.thumbnail_generator import ThumbnailGenerator

HISTORY_FILE = STORAGE_DIR / "history.json"

class ClippingPipeline:
    def __init__(self):
        self.downloader = VideoDownloader()
        self.transcriber = AudioTranscriber()
        self.facecam_detector = FacecamDetector()
        self.subtitle_gen = SubtitleGenerator()
        self.scorer = ViralityScorer()
        self.renderer = VideoRenderer()
        self.thumb_gen = ThumbnailGenerator()


    def _load_history(self) -> Dict[str, List[Dict[str, float]]]:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_history(self, history: Dict[str, List[Dict[str, float]]]):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def process_url(
        self,
        youtube_url: str,
        target_duration: int = 30,
        max_clips: int = 3,
        force_split_screen: Optional[bool] = None,
        manual_offset_seconds: Optional[int] = None,
        show_watermark: bool = False,
        show_headline: bool = True,
        show_captions: bool = True
    ) -> Dict[str, Any]:
        """
        Full end-to-end autonomous clipping pipeline.
        Includes history tracking so subsequent runs on the same stream URL
        automatically skip previously clipped moments and produce fresh highlights.
        """
        print(f"[Pipeline] Starting process for: {youtube_url} (Target duration: {target_duration}s)")

        # 1. Check history for repeated links to ensure NEW and DIFFERENT clips
        history = self._load_history()
        info_peek = self.downloader.extract_info(youtube_url)
        video_id = info_peek["id"]
        total_duration = info_peek.get("duration", 0)
        past_clips = history.get(video_id, [])

        # Determine dynamic fast-ingestion window (e.g. 3-5 mins is plenty for 3 viral shorts)
        window_minutes = max(3, min(6, int((max_clips * target_duration * 2.2) / 60) + 1))

        # Auto-advance scan window on subsequent runs
        if manual_offset_seconds is not None:
            start_offset = manual_offset_seconds
        else:
            run_number = len(past_clips) // max(1, max_clips)
            start_offset = min(600 + (run_number * window_minutes * 60), max(0, int(total_duration - (window_minutes * 60))))

        print(f"[Pipeline] Run #{len(past_clips)//max_clips + 1} for this stream. Scanning {window_minutes}m window starting at {start_offset}s (~{round(start_offset/60, 1)}m)...")

        # 2. Download Video, Audio, and Chat for this window in full 1080p
        download_result = self.downloader.download_video(
            youtube_url,
            start_offset_seconds=start_offset,
            window_minutes=window_minutes
        )
        video_path = download_result["video_path"]
        audio_path = download_result["audio_path"]
        chat_path = download_result["chat_path"]
        video_info = download_result["info"]
        uploader = video_info.get("uploader", "Streamer")

        # 3. Transcribe Audio (Word-level timestamps)
        transcript = self.transcriber.transcribe(audio_path)

        # 4. Detect Facecam and Gaming Layout in 1080p
        framing_info = self.facecam_detector.analyze_video(video_path)
        if force_split_screen is not None:
            framing_info["mode"] = "split_screen" if force_split_screen else "center_crop"

        # 5. Highlight & Viral Moment Detection
        detector = HighlightDetector(target_duration=target_duration)
        all_candidates = detector.find_highlights(transcript, chat_path=chat_path, max_clips=max_clips * 3)

        # Filter out any clips that overlap with previous runs
        candidate_clips = []
        for cand in all_candidates:
            abs_start = start_offset + cand["start"]
            abs_end = start_offset + cand["end"]

            already_clipped = False
            for prev in past_clips:
                if max(0, min(abs_end, prev["end"]) - max(abs_start, prev["start"])) > 8:
                    already_clipped = True
                    break

            if not already_clipped:
                candidate_clips.append(cand)
                if len(candidate_clips) >= max_clips:
                    break

        # Fallback if all candidates in window were taken: take remaining candidates
        if not candidate_clips and all_candidates:
            candidate_clips = all_candidates[:max_clips]

        print(f"[Pipeline] Found {len(candidate_clips)} fresh viral highlight segments.")

        # 6. Process & Render Each Candidate Clip
        rendered_clips = []
        clip_base_num = len(past_clips) + 1

        for idx, clip in enumerate(candidate_clips):
            clip_num = clip_base_num + idx
            clip_start = clip["start"]
            clip_end = clip["end"]
            clip_text = clip["text"]

            # Filter word-level timestamps for this clip
            clip_words = [
                w for w in transcript.get("all_words", [])
                if clip_start <= w["start"] <= clip_end
            ]

            # Evaluate Virality Score & Generate Viral Titles/Metadata
            virality_eval = self.scorer.evaluate_clip(
                text=clip_text,
                duration=clip["duration"],
                uploader=uploader
            )
            headline_text = virality_eval["selected_title"].split("(")[0].strip()

            # Generate Hormozi Animated ASS Subtitles with Center Headline Banner (and optional watermark)
            raw_ass_path = str(TEMP_DIR / f"{video_id}_clip_{clip_num}.ass")
            actual_ass = self.subtitle_gen.generate_ass(
                words=clip_words,
                output_path=raw_ass_path,
                clip_start=clip_start,
                clip_duration=clip["duration"],
                headline=headline_text,
                vertical_margin=360,
                uploader=uploader,
                show_watermark=show_watermark,
                show_headline=show_headline,
                show_captions=show_captions
            )

            # Render Final 1080p 9:16 Video
            output_clip_path = str(CLIPS_DIR / f"{video_id}_short_{clip_num}.mp4")
            self.renderer.render_short(
                input_video=video_path,
                start_time=clip_start,
                end_time=clip_end,
                framing_info=framing_info,
                subtitle_ass_path=actual_ass,
                output_path=output_clip_path,
                uploader=uploader
            )

            # Generate High-CTR Thumbnails (Vertical Short Cover + 16:9 Landscape)
            thumb_prefix = str(CLIPS_DIR / f"{video_id}_short_{clip_num}")
            thumbnails = self.thumb_gen.generate_thumbnails(
                video_path=output_clip_path,
                output_prefix=thumb_prefix,
                headline_text=headline_text,
                uploader=uploader
            )

            # Record in history
            past_clips.append({
                "clip_id": f"{video_id}_{clip_num}",
                "start": start_offset + clip_start,
                "end": start_offset + clip_end,
                "timestamp": output_clip_path
            })

            rendered_clips.append({
                "clip_id": f"{video_id}_{clip_num}",
                "clip_index": clip_num,
                "video_path": output_clip_path,
                "relative_video_path": f"/storage/clips/{video_id}_short_{clip_num}.mp4",
                "thumbnails": {
                    "vertical": f"/storage/clips/{video_id}_short_{clip_num}_thumb_vertical.jpg",
                    "landscape": f"/storage/clips/{video_id}_short_{clip_num}_thumb_landscape.jpg"
                },
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
                "hashtags_string": virality_eval.get("hashtags_string", " ".join(virality_eval["hashtags"])),
                "pinned_comment": virality_eval.get("pinned_comment", ""),
                "growth_tips": virality_eval.get("growth_tips", []),
                "layout_mode": framing_info["mode"],
                "status": "ready"
            })


        history[video_id] = past_clips
        self._save_history(history)

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

