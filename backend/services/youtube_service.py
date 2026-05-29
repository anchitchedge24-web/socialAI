import logging
import re
import json
import subprocess
from typing import Optional, Dict, Any
import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from utils.url_utils import extract_youtube_id
from models.video_metadata import VideoMetadata
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class YouTubeService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        self.api_key = settings.YOUTUBE_API_KEY
        self.api_base = "https://www.googleapis.com/youtube/v3"

    async def extract_metadata(self, url: str) -> VideoMetadata:
        video_id = extract_youtube_id(url)
        if not video_id:
            raise ValueError(f"Cannot extract YouTube video ID from: {url}")

        metadata = VideoMetadata(
            video_id="A",
            platform="youtube",
            url=url,
        )

        # 🎯 STRATEGY 1: YouTube Data API v3 (most reliable, accurate)
        if self.api_key:
            api_data = await self._extract_via_api(video_id)
            if api_data:
                self._populate_from_api(metadata, api_data, video_id)
                logger.info("✅ Used YouTube Data API v3 for metadata")
            else:
                logger.warning("YouTube API failed, falling back to yt-dlp")
                await self._fallback_extraction(url, video_id, metadata)
        else:
            logger.info("⚠️ YOUTUBE_API_KEY not set — using yt-dlp")
            await self._fallback_extraction(url, video_id, metadata)

        metadata.compute_engagement_rate()
        metadata.format_duration()

        # Get transcript
        transcript = await self.get_transcript(video_id)
        if transcript:
            metadata.transcript = transcript
            metadata.transcript_available = True

        return metadata

    async def _extract_via_api(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Fetch video metadata via YouTube Data API v3."""
        try:
            # Single API call to get video snippet + statistics + content details
            url = f"{self.api_base}/videos"
            params = {
                "id": video_id,
                "part": "snippet,statistics,contentDetails",
                "key": self.api_key,
            }

            response = await self.client.get(url, params=params)

            if response.status_code != 200:
                logger.warning(f"YouTube API returned {response.status_code}: {response.text[:300]}")
                return None

            data = response.json()
            items = data.get("items", [])

            if not items:
                logger.warning(f"YouTube API returned no items for video {video_id}")
                return None

            video_data = items[0]

            # Optionally fetch channel info for follower count
            channel_id = video_data.get("snippet", {}).get("channelId")
            channel_info = None
            if channel_id:
                channel_info = await self._fetch_channel_info(channel_id)

            video_data["_channel_info"] = channel_info
            return video_data

        except httpx.TimeoutException:
            logger.warning("YouTube API request timed out")
            return None
        except Exception as e:
            logger.warning(f"YouTube API error: {e}")
            return None

    async def _fetch_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Fetch channel info (for subscriber count)."""
        try:
            url = f"{self.api_base}/channels"
            params = {
                "id": channel_id,
                "part": "statistics",
                "key": self.api_key,
            }
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                items = response.json().get("items", [])
                if items:
                    return items[0]
        except Exception as e:
            logger.debug(f"Channel info fetch failed: {e}")
        return None

    def _populate_from_api(self, metadata: VideoMetadata, data: dict, video_id: str):
        """Populate metadata from YouTube API response."""
        snippet = data.get("snippet", {})
        statistics = data.get("statistics", {})
        content_details = data.get("contentDetails", {})
        channel_info = data.get("_channel_info") or {}

        # Title & description
        metadata.title = snippet.get("title", "Unknown")
        metadata.description = (snippet.get("description") or "")[:500]

        # Creator info
        metadata.creator_name = snippet.get("channelTitle", "Unknown")

        # Statistics (always present, sometimes "0")
        metadata.views = int(statistics.get("viewCount", 0))
        metadata.likes = int(statistics.get("likeCount", 0))
        metadata.comments = int(statistics.get("commentCount", 0))

        # Channel follower count
        if channel_info:
            channel_stats = channel_info.get("statistics", {})
            sub_count = channel_stats.get("subscriberCount")
            if sub_count:
                metadata.follower_count = int(sub_count)

        # Duration (ISO 8601 format: PT4M13S → 253 seconds)
        duration_iso = content_details.get("duration", "PT0S")
        metadata.duration = self._parse_iso8601_duration(duration_iso)

        # Thumbnail (try highest quality available)
        thumbnails = snippet.get("thumbnails", {})
        thumb_priority = ["maxres", "high", "medium", "default"]
        for quality in thumb_priority:
            if quality in thumbnails:
                metadata.thumbnail = thumbnails[quality].get("url", "")
                break
        if not metadata.thumbnail:
            metadata.thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        # Upload date (ISO 8601 → YYYY-MM-DD)
        published_at = snippet.get("publishedAt", "")
        if published_at:
            metadata.upload_date = published_at[:10]  # "2024-01-15T10:30:00Z" → "2024-01-15"

        # Hashtags from description + tags
        hashtags = set()
        desc = snippet.get("description", "")
        if desc:
            hashtags.update(re.findall(r"#(\w+)", desc))
        tags = snippet.get("tags", []) or []
        for tag in tags[:10]:  # limit to 10 tags
            hashtags.add(tag.replace(" ", ""))
        metadata.hashtags = list(hashtags)[:15]

        logger.info(
            f"📊 YouTube API metrics — "
            f"Views: {metadata.views:,} | "
            f"Likes: {metadata.likes:,} | "
            f"Comments: {metadata.comments:,} | "
            f"Subs: {metadata.follower_count or 'N/A'}"
        )

    def _parse_iso8601_duration(self, iso: str) -> float:
        """Parse ISO 8601 duration (PT4M13S) to seconds."""
        try:
            pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
            match = re.match(pattern, iso)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return float(hours * 3600 + minutes * 60 + seconds)
        except Exception:
            pass
        return 0.0

    async def _fallback_extraction(self, url: str, video_id: str, metadata: VideoMetadata):
        """Fallback chain: yt-dlp → scraping."""
        # Try yt-dlp first
        ytdlp_data = await self._extract_with_ytdlp(url)
        if ytdlp_data:
            logger.info("✅ Used yt-dlp for YouTube metadata (fallback)")
            metadata.title = ytdlp_data.get("title") or "Unknown"
            metadata.description = (ytdlp_data.get("description") or "")[:500]
            metadata.creator_name = ytdlp_data.get("uploader") or ytdlp_data.get("channel") or "Unknown"
            metadata.views = int(ytdlp_data.get("view_count") or 0)
            metadata.likes = int(ytdlp_data.get("like_count") or 0)
            metadata.comments = int(ytdlp_data.get("comment_count") or 0)
            metadata.duration = float(ytdlp_data.get("duration") or 0)
            metadata.thumbnail = ytdlp_data.get("thumbnail") or f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            metadata.follower_count = ytdlp_data.get("channel_follower_count")

            raw_date = ytdlp_data.get("upload_date") or ""
            if raw_date and len(raw_date) == 8 and raw_date.isdigit():
                metadata.upload_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

            desc = ytdlp_data.get("description") or ""
            if desc:
                metadata.hashtags = re.findall(r"#(\w+)", desc)
        else:
            logger.warning("yt-dlp failed, falling back to oEmbed + scraping")
            await self._extract_via_scraping(url, video_id, metadata)

        # Estimate missing engagement
        if metadata.likes == 0 and metadata.views > 0:
            metadata.likes = int(metadata.views * 0.04)
        if metadata.comments == 0 and metadata.views > 0:
            metadata.comments = int(metadata.views * 0.005)

    async def _extract_with_ytdlp(self, url: str) -> Optional[Dict[str, Any]]:
        """yt-dlp fallback."""
        try:
            cmd = [
                "yt-dlp",
                "--dump-json", "--no-download", "--no-check-certificates",
                "--no-warnings", "--ignore-errors", "--quiet", "--no-playlist",
                "--extractor-args", "youtube:player_client=web",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                url,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout.strip().split("\n")[0])
            return None
        except Exception as e:
            logger.warning(f"yt-dlp error: {e}")
            return None

    async def _extract_via_scraping(self, url: str, video_id: str, metadata: VideoMetadata):
        """Last resort: scrape YouTube page."""
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            resp = await self.client.get(oembed_url)
            if resp.status_code == 200:
                oembed = resp.json()
                metadata.title = oembed.get("title", metadata.title)
                metadata.creator_name = oembed.get("author_name", metadata.creator_name)
                metadata.thumbnail = oembed.get("thumbnail_url", f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
        except Exception as e:
            logger.warning(f"oEmbed failed: {e}")

        if not metadata.thumbnail:
            metadata.thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    async def get_transcript(self, video_id: str) -> Optional[str]:
        """Try multiple transcript fetch strategies."""
        from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

        # Strategy 1: youtube-transcript-api
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
            segments = [e.get("text", "").strip() for e in transcript_list if e.get("text", "").strip()]
            if segments:
                logger.info("✅ Got transcript via youtube-transcript-api")
                return " ".join(segments)
        except (TranscriptsDisabled, NoTranscriptFound):
            logger.warning(f"No captions available for {video_id}")
            return None
        except Exception as e:
            logger.warning(f"youtube-transcript-api failed: {str(e)[:200]}")

        # Strategy 2: yt-dlp subtitles
        try:
            transcript = await self._get_transcript_via_ytdlp(video_id)
            if transcript:
                logger.info("✅ Got transcript via yt-dlp")
                return transcript
        except Exception as e:
            logger.warning(f"yt-dlp transcript fallback failed: {e}")

        logger.warning(f"❌ All transcript strategies failed for {video_id}")
        return None

    async def _get_transcript_via_ytdlp(self, video_id: str) -> Optional[str]:
        """Get auto-generated subtitles via yt-dlp."""
        import tempfile
        import os
        import glob

        url = f"https://www.youtube.com/watch?v={video_id}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                cmd = [
                    "yt-dlp", "--skip-download", "--write-auto-subs", "--write-subs",
                    "--sub-langs", "en.*", "--sub-format", "vtt",
                    "--output", os.path.join(tmp_dir, "%(id)s.%(ext)s"),
                    "--no-warnings", "--quiet", url,
                ]
                subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                vtt_files = glob.glob(os.path.join(tmp_dir, "*.vtt"))
                if not vtt_files:
                    return None

                with open(vtt_files[0], "r", encoding="utf-8") as f:
                    vtt_content = f.read()

                lines = []
                for line in vtt_content.split("\n"):
                    line = line.strip()
                    if (not line or line == "WEBVTT" or "-->" in line or
                        line.startswith(("Kind:", "Language:", "NOTE"))):
                        continue
                    line = re.sub(r"<[^>]+>", "", line)
                    if line:
                        lines.append(line)

                cleaned = []
                prev = None
                for line in lines:
                    if line != prev:
                        cleaned.append(line)
                        prev = line

                transcript = " ".join(cleaned)
                return transcript if transcript else None

            except Exception as e:
                logger.warning(f"yt-dlp subtitle parse error: {e}")
                return None

    async def close(self):
        await self.client.aclose()