import re
from typing import Dict, Any, List

class ViralityScorer:
    def evaluate_clip(self, text: str, duration: float, uploader: str = "Streamer") -> Dict[str, Any]:
        """
        Evaluates clip transcript and generates virality rating,
        optimized YouTube Shorts title, description, and hashtags.
        """
        clean_text = text.strip()
        words = clean_text.split()
        word_count = len(words)

        # 1. Component Scores
        # Hook strength (opening 5 words)
        hook_score = 70.0
        first_few = " ".join(words[:6]).lower()
        if any(w in first_few for w in ["what", "how", "why", "wait", "no", "look", "watch", "omg", "holy"]):
            hook_score = 92.0
        elif any(w in first_few for w in ["i", "he", "she", "they", "this", "never", "always"]):
            hook_score = 82.0

        # Emotional Intensity
        emotion_score = 65.0
        lower_all = clean_text.lower()
        hot_words = ["insane", "crazy", "dead", "win", "clutch", "holy", "hack", "omg", "wtf", "lmao", "cheat"]
        found_hot = [hw for hw in hot_words if hw in lower_all]
        emotion_score = min(98.0, 65.0 + len(found_hot) * 8.0)

        # Narrative Flow / Coherence
        flow_score = 75.0
        if 20 <= word_count <= 80:
            flow_score = 88.0
        elif word_count < 15:
            flow_score = 60.0

        # Loop / Rewatchability
        loop_score = round((hook_score * 0.4 + emotion_score * 0.4 + flow_score * 0.2), 1)
        total_virality_rate = round((hook_score * 0.35 + emotion_score * 0.3 + flow_score * 0.2 + loop_score * 0.15), 1)

        # 2. Generate Viral Titles
        titles = self._generate_titles(clean_text, uploader, found_hot)

        # 3. Generate Viral Description & Hashtags
        hashtags = ["#shorts", "#viral", "#gaming", f"#{uploader.lower().replace(' ', '')}", "#funny", "#trending", "#youtubeshorts"]
        description = (
            f"{titles[0]}\n\n"
            f"Watch the most insane moments and highlights! 🔥\n"
            f"Credit: {uploader}\n\n"
            f"{' '.join(hashtags)}"
        )

        return {
            "virality_rate": total_virality_rate,
            "breakdown": {
                "hook_strength": hook_score,
                "emotional_intensity": emotion_score,
                "narrative_flow": flow_score,
                "rewatchability": loop_score
            },
            "suggested_titles": titles,
            "selected_title": titles[0],
            "description": description,
            "hashtags": hashtags
        }

    def _generate_titles(self, text: str, uploader: str, hot_words: List[str]) -> List[str]:
        """Generates punchy curiosity-gap titles."""
        clean_snip = " ".join(text.split()[:8])
        clean_snip = re.sub(r'[^a-zA-Z0-9\s]', '', clean_snip).strip()

        titles = []
        if hot_words:
            titles.append(f"He ACTUALLY Did This... 💀 ({uploader})")
            titles.append(f"The Most {hot_words[0].upper()} Moment Ever! 😱")
            titles.append(f"Wait For The End... You Won't Believe It 🔥")
        else:
            titles.append(f"When {uploader} Realized What Happened... 🤯")
            titles.append(f"This Might Be The Best Moment Yet! 🚀")
            titles.append(f"{clean_snip.title()}... 👀")

        return titles
