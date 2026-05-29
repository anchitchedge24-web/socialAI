import logging
from models.video_metadata import VideoMetadata

logger = logging.getLogger(__name__)


class EngagementService:
    @staticmethod
    def compute_engagement(metadata: VideoMetadata) -> float:
        if metadata.views > 0:
            rate = ((metadata.likes + metadata.comments) / metadata.views) * 100
            metadata.engagement_rate = round(rate, 4)
        else:
            metadata.engagement_rate = 0.0
        return metadata.engagement_rate

    @staticmethod
    def compare_engagement(video_a: VideoMetadata, video_b: VideoMetadata) -> dict:
        return {
            "video_a": {
                "engagement_rate": video_a.engagement_rate,
                "views": video_a.views,
                "likes": video_a.likes,
                "comments": video_a.comments,
            },
            "video_b": {
                "engagement_rate": video_b.engagement_rate,
                "views": video_b.views,
                "likes": video_b.likes,
                "comments": video_b.comments,
            },
            "winner": "A" if video_a.engagement_rate > video_b.engagement_rate else "B",
            "difference": round(abs(video_a.engagement_rate - video_b.engagement_rate), 4),
        }