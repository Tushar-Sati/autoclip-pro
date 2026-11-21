import json
import re
from typing import List, Dict, Any, Optional
import numpy as np

VIRAL_KEYWORDS = {
    "lol", "lmao", "omg", "wtf", "pog", "poggers", "holy", "insane", "clip", "no way",
    "dead", "died", "kill", "win", "clutch", "crazy", "goat", "w", "hack", "secret", "reveal"
}

HOOK_TRIGGERS = [
    r"\b(i can't believe|look at this|watch this|listen to this|wait what|did you see|holy shit)\b",
    r"\b(the truth about|the real reason|nobody knows|here's why|don't ever|what happens if)\b",
    r"\b(this is insane|how did|why did|what the|are you serious)\b"
]

class HighlightDetector:
    def __init__(self, target_duration: int = 30):
        self.target_duration = target_duration

    def find_highlights(
        self,
        transcript_data: Dict[str, Any],
        chat_path: Optional[str] = None,
        max_clips: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyzes transcript and chat logs to extract the best candidate clips
        around the requested target duration.
        """
        segments = transcript_data.get("segments", [])
        total_duration = transcript_data.get("duration", 0)

        if not segments:
            # Fallback if no speech: return evenly spaced intervals
            return self._fallback_intervals(total_duration, max_clips)

        # 1. Parse chat spikes if available
        chat_spikes = {}
        if chat_path:
            chat_spikes = self._analyze_chat_spikes(chat_path, bin_size=15)

        # 2. Build candidate windows centered around high-energy segments
        candidates = []
        step_seconds = 10 # slide every 10 seconds

        current_start = 0.0
        while current_start + self.target_duration <= total_duration:
            current_end = current_start + self.target_duration
            
            # Find words/segments falling inside this window
            window_segments = [s for s in segments if s["end"] >= current_start and s["start"] <= current_end]
            if not window_segments:
                current_start += step_seconds
                continue

            # Snap start to the beginning of the closest sentence/segment
            snapped_start = window_segments[0]["start"]
            snapped_end = window_segments[-1]["end"]
            
            # Ensure duration is reasonably close to target
            clip_duration = snapped_end - snapped_start
            if clip_duration < 10:
                current_start += step_seconds
                continue

            window_text = " ".join([s["text"] for s in window_segments])

            # Calculate Scores
            # Score 1: Chat spike boost (0 to 40)
            chat_score = 0.0
            mid_time = int((snapped_start + snapped_end) / 2)
            time_bin = (mid_time // 15) * 15
            if time_bin in chat_spikes:
                chat_score = min(40.0, chat_spikes[time_bin] * 5.0)

            # Score 2: Speech energy & word density (0 to 30)
            total_words = sum([len(s.get("words", [])) for s in window_segments])
            wpm = (total_words / (clip_duration / 60)) if clip_duration > 0 else 0
            # Sweet spot is 130 - 180 WPM
            speech_score = 30.0 if 130 <= wpm <= 200 else (20.0 if wpm > 80 else 10.0)

            # Score 3: Hook & Viral Keyword presence (0 to 30)
            keyword_score = 0.0
            text_lower = window_text.lower()
            
            # Check for hook triggers in the first 5 seconds
            first_5s_text = " ".join([s["text"] for s in window_segments if s["start"] <= snapped_start + 5.0]).lower()
            for pattern in HOOK_TRIGGERS:
                if re.search(pattern, first_5s_text):
                    keyword_score += 15.0
                    break

            for kw in VIRAL_KEYWORDS:
                if kw in text_lower:
                    keyword_score = min(30.0, keyword_score + 3.0)

            total_score = min(100.0, chat_score + speech_score + keyword_score)

            candidates.append({
                "start": round(snapped_start, 2),
                "end": round(snapped_end, 2),
                "duration": round(clip_duration, 2),
                "text": window_text,
                "score": round(total_score, 1),
                "chat_score": round(chat_score, 1),
                "speech_score": round(speech_score, 1),
                "keyword_score": round(keyword_score, 1)
            })

            current_start += step_seconds

        # 3. Non-maximum suppression (remove overlapping clips)
        sorted_candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        selected_clips = []

        for cand in sorted_candidates:
            # Check overlap with already selected
            overlap = False
            for sel in selected_clips:
                # If they overlap by more than 8 seconds
                if max(0, min(cand["end"], sel["end"]) - max(cand["start"], sel["start"])) > 8:
                    overlap = True
                    break
            if not overlap:
                selected_clips.append(cand)
                if len(selected_clips) >= max_clips:
                    break

        # Sort chronologically
        selected_clips.sort(key=lambda x: x["start"])
        return selected_clips

    def _analyze_chat_spikes(self, chat_path: str, bin_size: int = 15) -> Dict[int, float]:
        """Calculates normalized chat message velocity per time bin."""
        try:
            with open(chat_path, "r", encoding="utf-8") as f:
                messages = json.load(f)
            
            if not messages:
                return {}

            bins = {}
            for msg in messages:
                t = int(msg.get("time_in_seconds", 0))
                bin_key = (t // bin_size) * bin_size
                text = msg.get("message", "").lower()
                
                # Weight by message count + emote weight
                weight = 1.0
                for kw in VIRAL_KEYWORDS:
                    if kw in text:
                        weight += 1.5
                bins[bin_key] = bins.get(bin_key, 0.0) + weight

            if not bins:
                return {}

            vals = list(bins.values())
            mean = np.mean(vals)
            std = np.std(vals) if np.std(vals) > 0 else 1.0

            # Compute z-scores
            z_scores = {k: max(0.0, (v - mean) / std) for k, v in bins.items()}
            return z_scores
        except Exception as e:
            print(f"[HighlightDetector] Chat parsing error: {e}")
            return {}

    def _fallback_intervals(self, total_duration: float, max_clips: int) -> List[Dict[str, Any]]:
        """Fallback when no speech is detected."""
        clips = []
        step = max(self.target_duration, total_duration / (max_clips + 1))
        t = step
        while t + self.target_duration <= total_duration and len(clips) < max_clips:
            clips.append({
                "start": round(t, 2),
                "end": round(t + self.target_duration, 2),
                "duration": self.target_duration,
                "text": "Highlight segment",
                "score": 75.0,
                "chat_score": 0.0,
                "speech_score": 0.0,
                "keyword_score": 0.0
            })
            t += step * 1.5
        return clips
