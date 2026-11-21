from typing import List, Dict, Any
from faster_whisper import WhisperModel
from backend.app.config import settings

class AudioTranscriber:
    def __init__(self, model_size: str = settings.whisper_model_size, device: str = settings.device, compute_type: str = settings.compute_type):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def _load_model(self):
        if self.model is None:
            print(f"[Transcriber] Loading faster-whisper model ({self.model_size}) on {self.device}...")
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio with word-level timestamps."""
        self._load_model()
        print(f"[Transcriber] Transcribing {audio_path}...")
        segments_generator, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True, # Voice Activity Detection to filter background noise
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        segments = []
        all_words = []

        for seg in segments_generator:
            seg_words = []
            if seg.words:
                for w in seg.words:
                    word_obj = {
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 3)
                    }
                    seg_words.append(word_obj)
                    all_words.append(word_obj)

            segments.append({
                "id": seg.id,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
                "words": seg_words
            })

        print(f"[Transcriber] Finished. Detected {len(segments)} segments, {len(all_words)} words.")
        return {
            "language": info.language,
            "duration": round(info.duration, 2),
            "segments": segments,
            "all_words": all_words
        }
