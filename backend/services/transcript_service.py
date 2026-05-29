import logging
import os
from typing import Optional
from utils.text_utils import clean_transcript

logger = logging.getLogger(__name__)

# Try to import whisper — gracefully fail if not installed (production)
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("⚠️ Whisper not installed — audio transcription disabled (this is normal in production)")


class TranscriptService:
    def __init__(self, whisper_model_name: str = "base"):
        self.whisper_model_name = whisper_model_name
        self._whisper_model = None

    def _get_whisper_model(self):
        if not WHISPER_AVAILABLE:
            raise RuntimeError(
                "Whisper is not installed. Install with: pip install openai-whisper"
            )

        if self._whisper_model is None:
            logger.info(f"Loading Whisper model: {self.whisper_model_name}")
            self._whisper_model = whisper.load_model(self.whisper_model_name)
            logger.info("Whisper model loaded successfully")
        return self._whisper_model

    async def transcribe_audio(self, audio_path: str) -> Optional[str]:
        if not WHISPER_AVAILABLE:
            logger.warning("⚠️ Whisper not available — skipping transcription")
            return None

        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None

        try:
            model = self._get_whisper_model()
            logger.info(f"Transcribing: {audio_path}")
            result = model.transcribe(audio_path, language="en")
            transcript = result.get("text", "")
            transcript = clean_transcript(transcript)
            logger.info(f"Transcription complete: {len(transcript)} chars")
            return transcript
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return None

    async def transcribe_with_timestamps(self, audio_path: str):
        if not WHISPER_AVAILABLE or not os.path.exists(audio_path):
            return []

        try:
            model = self._get_whisper_model()
            result = model.transcribe(audio_path, language="en")
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "text": seg["text"].strip(),
                    "start": seg["start"],
                    "end": seg["end"],
                })
            return segments
        except Exception as e:
            logger.error(f"Whisper timestamp transcription failed: {e}")
            return []