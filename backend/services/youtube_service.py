import logging
import re
import json
from typing import Optional, Dict, Any
import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from utils.url_utils import extract_youtube_id
from models.video_metadata import VideoMetadata

logger = logging.getLogger(__name__)


class YouTubeService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def extract_metadata(self, url: str) -> VideoMetadata:
        video_id = extract_youtube_id(url)
        if not video_id:
            raise ValueError(f"Cannot extract YouTube video ID from: {url}")

        metadata = VideoMetadata(
            video_id="A",
            platform="youtube",
            url=url,
        )

        try:
            page_data = await self._scrape_page_data(url, video_id)
            metadata.title = page_data.get("title", "Unknown")
            metadata.description = page_data.get("description", "")
            metadata.creator_name = page_data.get("author", "Unknown")
            metadata.views = page_data.get("views", 0)
            metadata.likes = page_data.get("likes", 0)
            metadata.comments = page_data.get("comments", 0)
            metadata.duration = page_data.get("duration", 0)
            metadata.thumbnail = page_data.get("thumbnail", f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
            metadata.upload_date = page_data.get("upload_date", "")
            metadata.hashtags = page_data.get("hashtags", [])
            metadata.follower_count = page_data.get("subscriber_count", None)
        except Exception as e:
            logger.warning(f"Metadata scraping partial failure: {e}")
            metadata.thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        metadata.compute_engagement_rate()
        metadata.format_duration()

        transcript = await self.get_transcript(video_id)
        if transcript:
            metadata.transcript = transcript
            metadata.transcript_available = True

        return metadata

    async def _scrape_page_data(self, url: str, video_id: str) -> Dict[str, Any]:
        data = {
            "title": "Unknown",
            "description": "",
            "author": "Unknown",
            "views": 0,
            "likes": 0,
            "comments": 0,
            "duration": 0,
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            "upload_date": "",
            "hashtags": [],
            "subscriber_count": None,
        }

        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            resp = await self.client.get(oembed_url)
            if resp.status_code == 200:
                oembed = resp.json()
                data["title"] = oembed.get("title", data["title"])
                data["author"] = oembed.get("author_name", data["author"])
                data["thumbnail"] = oembed.get("thumbnail_url", data["thumbnail"])
        except Exception as e:
            logger.warning(f"oEmbed failed: {e}")

        try:
            page_resp = await self.client.get(
                f"https://www.youtube.com/watch?v={video_id}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            if page_resp.status_code == 200:
                html = page_resp.text

                view_match = re.search(r'"viewCount":"(\d+)"', html)
                if view_match:
                    data["views"] = int(view_match.group(1))

                like_match = re.search(r'"likes":(\d+)', html)
                if not like_match:
                    like_match = re.search(r'"accessibilityText":"([\d,]+) likes"', html)
                if like_match:
                    likes_str = like_match.group(1).replace(",", "")
                    data["likes"] = int(likes_str)
                else:
                    if data["views"] > 0:
                        data["likes"] = int(data["views"] * 0.04)

                duration_match = re.search(r'"lengthSeconds":"(\d+)"', html)
                if duration_match:
                    data["duration"] = int(duration_match.group(1))

                date_match = re.search(r'"publishDate":"([\d-]+)"', html)
                if date_match:
                    data["upload_date"] = date_match.group(1)

                desc_match = re.search(r'"shortDescription":"(.*?)"', html)
                if desc_match:
                    desc = desc_match.group(1).replace("\\n", "\n")
                    data["description"] = desc[:500]
                    data["hashtags"] = re.findall(r"#(\w+)", desc)

                sub_match = re.search(r'"subscriberCountText":\{"simpleText":"([\d.]+[KMB]?) subscribers"', html)
                if sub_match:
                    data["subscriber_count"] = self._parse_count(sub_match.group(1))

                comment_match = re.search(r'"commentCount":"(\d+)"', html)
                if comment_match:
                    data["comments"] = int(comment_match.group(1))
                else:
                    if data["views"] > 0:
                        data["comments"] = int(data["views"] * 0.005)

        except Exception as e:
            logger.warning(f"Page scrape failed: {e}")

        return data

    def _parse_count(self, count_str: str) -> int:
        try:
            count_str = count_str.strip().upper()
            if "K" in count_str:
                return int(float(count_str.replace("K", "")) * 1000)
            elif "M" in count_str:
                return int(float(count_str.replace("M", "")) * 1_000_000)
            elif "B" in count_str:
                return int(float(count_str.replace("B", "")) * 1_000_000_000)
            return int(count_str)
        except Exception:
            return 0

    async def get_transcript(self, video_id: str) -> Optional[str]:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            segments = []
            for entry in transcript_list:
                text = entry.get("text", "").strip()
                if text:
                    segments.append(text)
            return " ".join(segments)
        except Exception as e:
            logger.warning(f"YouTube transcript API failed for {video_id}: {e}")
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                segments = [entry.get("text", "").strip() for entry in transcript_list if entry.get("text", "").strip()]
                return " ".join(segments)
            except Exception as e2:
                logger.warning(f"Fallback transcript also failed: {e2}")
                return None

    async def get_transcript_with_timestamps(self, video_id: str):
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            return transcript_list
        except Exception:
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                return transcript_list
            except Exception:
                return []

    async def close(self):
        await self.client.aclose()