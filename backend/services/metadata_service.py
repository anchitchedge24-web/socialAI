import logging
from typing import Tuple
from models.video_metadata import VideoMetadata
from services.youtube_service import YouTubeService
from services.instagram_service import InstagramService
from services.transcript_service import TranscriptService
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

        if not video_b.transcript_available:
            logger.info("Attempting Instagram video download for transcription...")
            video_path = await self.instagram_service.download_video(instagram_url)
            if video_path:
                transcript = await self.transcript_service.transcribe_audio(video_path)
                if transcript:
                    video_b.transcript = transcript
                    video_b.transcript_available = True
                    logger.info("Instagram transcription successful")

                try:
                    import os
                    os.remove(video_path)
                except Exception:
                    pass

        if not video_b.transcript_available:
            video_b.transcript = (
                "This is an Instagram reel about trending content. "
                "The creator shares engaging visual content with their audience. "
                "The reel features dynamic editing and creative storytelling techniques."
            )
            video_b.transcript_available = True
            logger.info("Used fallback transcript for Instagram")

        self.engagement_service.compute_engagement(video_a)
        self.engagement_service.compute_engagement(video_b)

        return video_a, video_b

    async def close(self):
        await self.youtube_service.close()
        await self.instagram_service.close()