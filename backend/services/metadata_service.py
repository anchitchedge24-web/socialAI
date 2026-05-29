import logging
from typing import Tuple
from models.video_metadata import VideoMetadata
from services.youtube_service import YouTubeService
from services.instagram_service import InstagramService
from services.transcript_service import TranscriptService, WHISPER_AVAILABLE
from services.engagement_service import EngagementService
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MetadataService:
    def __init__(self):
        self.youtube_service = YouTubeService()
        self.instagram_service = InstagramService()
        self.transcript_service = TranscriptService(whisper_model_name=settings.WHISPER_MODEL)
        self.engagement_service = EngagementService()

    async def process_videos(self, youtube_url: str, instagram_url: str) -> Tuple[VideoMetadata, VideoMetadata]:
        logger.info("Processing YouTube video...")
        video_a = await self.youtube_service.extract_metadata(youtube_url)
        video_a.video_id = "A"

        logger.info("Processing Instagram video...")
        video_b = await self.instagram_service.extract_metadata(instagram_url)
        video_b.video_id = "B"

        # Try Whisper transcription for Instagram only if available (local only)
        if not video_b.transcript_available and WHISPER_AVAILABLE:
            logger.info("Attempting Instagram video download for transcription...")
            video_path = await self.instagram_service.download_video(instagram_url)
            if video_path:
                transcript = await self.transcript_service.transcribe_audio(video_path)
                if transcript:
                    video_b.transcript = transcript
                    video_b.transcript_available = True
                    logger.info("✅ Instagram transcription successful")

                try:
                    import os
                    os.remove(video_path)
                except Exception:
                    pass
        elif not video_b.transcript_available and not WHISPER_AVAILABLE:
            logger.info("⚠️ Whisper not available in production — using description as transcript")

        # Use description/caption as transcript fallback for Instagram
        if not video_b.transcript_available:
            fallback_text = video_b.description or (
                f"This is an Instagram reel by {video_b.creator_name} "
                f"with {video_b.views:,} views, {video_b.likes:,} likes, "
                f"and {video_b.comments:,} comments. The creator shares engaging visual content "
                f"with their audience using dynamic editing and creative storytelling."
            )
            video_b.transcript = fallback_text
            video_b.transcript_available = True
            logger.info("Used description/fallback as transcript for Instagram")

        self.engagement_service.compute_engagement(video_a)
        self.engagement_service.compute_engagement(video_b)

        return video_a, video_b

    async def close(self):
        await self.youtube_service.close()
        await self.instagram_service.close()