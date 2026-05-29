import logging
import re
import json
import subprocess
from typing import Optional, Dict, Any
import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from utils.url_utils import extract_youtube_id
from models.video_metadata import VideoMetadata

logger = logging.getLogger(__name__)


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

    async def extract_metadata(self, url: str) -> VideoMetadata:
        video_id = extract_youtube_id(url)
        if not video_id:
            raise ValueError(f"Cannot extract YouTube video ID from: {url}")

        metadata = VideoMetadata(
            video_id="A",
            platform="youtube",
            url=url,
        )

        # 🎯 Try yt-dlp FIRST (works on Render where direct scraping fails)
        ytdlp_data = await self._extract_with_ytdlp(url)

        if ytdlp_data:
            logger.info("✅ Used yt-dlp for YouTube metadata")
            metadata.title = ytdlp_data.get("title") or "Unknown"
            metadata.description = (ytdlp_data.get("description") or "")[:500]
            metadata.creator_name = ytdlp_data.get("uploader") or ytdlp_data.get("channel") or "Unknown"
            metadata.views = int(ytdlp_data.get("view_count") or 0)
            metadata.likes = int(ytdlp_data.get("like_count") or 0)
            metadata.comments = int(ytdlp_data.get("comment_count") or 0)
            metadata.duration = float(ytdlp_data.get("duration") or 0)
            metadata.thumbnail = ytdlp_data.get("thumbnail") or f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            metadata.follower_count = ytdlp_data.get("channel_follower_count")

            # Format upload date YYYYMMDD → YYYY-MM-DD
            raw_date = ytdlp_data.get("upload_date") or ""
            if raw_date and len(raw_date) == 8 and raw_date.isdigit():
                metadata.upload_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
            else:
                metadata.upload_date = raw_date

            # Extract hashtags from description
            desc = ytdlp_data.get("description") or ""
            if desc:
                metadata.hashtags = re.findall(r"#(\w+)", desc)

            # Get transcript from yt-dlp's auto-subs if available
            subs = ytdlp_data.get("subtitles", {}) or {}
            auto_subs = ytdlp_data.get("automatic_captions", {}) or {}

            # Estimate likes from views if missing
            if metadata.likes == 0 and metadata.views > 0:
                metadata.likes = int(metadata.views * 0.04)
            if metadata.comments == 0 and metadata.views > 0:
                metadata.comments = int(metadata.views * 0.005)
        else:
            logger.warning("yt-dlp failed, falling back to oEmbed + scraping")
            await self._extract_via_scraping(url, video_id, metadata)

        metadata.compute_engagement_rate()
        metadata.format_duration()

        # Try to get transcript (multiple strategies)
        transcript = await self.get_transcript(video_id)
        if transcript:
            metadata.transcript = transcript
            metadata.transcript_available = True

        return metadata

    async def _extract_with_ytdlp(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract metadata using yt-dlp (more reliable on cloud servers)."""
        try:
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--no-check-certificates",
                "--no-warnings",
                "--ignore-errors",
                "--quiet",
                "--no-playlist",
                url,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="replace",
            )

            if result.returncode == 0 and result.stdout.strip():
                first_line = result.stdout.strip().split("\n")[0]
                return json.loads(first_line)
            else:
                logger.warning(f"yt-dlp YouTube extract failed: {(result.stderr or '')[:300]}")
                return None
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp YouTube extract timed out")
            return None
        except Exception as e:
            logger.warning(f"yt-dlp YouTube extract error: {e}")
            return None

    async def _extract_via_scraping(self, url: str, video_id: str, metadata: VideoMetadata):
        """Fallback: scrape YouTube page directly (works locally, often fails on cloud)."""
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            resp = await self.client.get(oembed_url)
            if resp.status_code == 200:
                oembed = resp.json()
                metadata.title = oembed.get("title", metadata.title)
                metadata.creator_name = oembed.get("author_name", metadata.creator_name)
                metadata.thumbnail = oembed.get("thumbnail_url", metadata.thumbnail)
        except Exception as e:
            logger.warning(f"oEmbed failed: {e}")

        # Set thumbnail fallback
        if not metadata.thumbnail:
            metadata.thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        # Try to scrape watch page (often blocked on cloud)
        try:
            page_resp = await self.client.get(f"https://www.youtube.com/watch?v={video_id}")
            if page_resp.status_code == 200:
                html = page_resp.text
                view_match = re.search(r'"viewCount":"(\d+)"', html)
                if view_match:
                    metadata.views = int(view_match.group(1))

                duration_match = re.search(r'"lengthSeconds":"(\d+)"', html)
                if duration_match:
                    metadata.duration = int(duration_match.group(1))

                # Estimate engagement
                if metadata.views > 0:
                    metadata.likes = int(metadata.views * 0.04)
                    metadata.comments = int(metadata.views * 0.005)
        except Exception as e:
            logger.warning(f"Page scrape failed: {e}")

    async def get_transcript(self, video_id: str) -> Optional[str]:
        """Try multiple transcript fetch strategies."""
        from youtube_transcript_api._errors import (
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )

        # Strategy 1: Direct youtube-transcript-api (works locally)
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
            segments = [e.get("text", "").strip() for e in transcript_list if e.get("text", "").strip()]
            if segments:
                logger.info("✅ Got transcript via youtube-transcript-api")
                return " ".join(segments)
        except (TranscriptsDisabled, NoTranscriptFound):
            logger.warning(f"No captions for {video_id}")
            return None
        except Exception as e:
            logger.warning(f"youtube-transcript-api failed: {str(e)[:200]}")

        # Strategy 2: Use yt-dlp to get subtitles (works on cloud)
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
                    "yt-dlp",
                    "--skip-download",
                    "--write-auto-subs",
                    "--write-subs",
                    "--sub-langs", "en.*",
                    "--sub-format", "vtt",
                    "--output", os.path.join(tmp_dir, "%(id)s.%(ext)s"),
                    "--no-warnings",
                    "--quiet",
                    url,
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                # Find any .vtt file in the temp dir
                vtt_files = glob.glob(os.path.join(tmp_dir, "*.vtt"))
                if not vtt_files:
                    return None

                with open(vtt_files[0], "r", encoding="utf-8") as f:
                    vtt_content = f.read()

                # Parse VTT: extract text lines only
                lines = []
                for line in vtt_content.split("\n"):
                    line = line.strip()
                    # Skip headers, timestamps, empty lines
                    if (not line or
                        line == "WEBVTT" or
                        "-->" in line or
                        line.startswith("Kind:") or
                        line.startswith("Language:") or
                        line.startswith("NOTE")):
                        continue
                    # Remove VTT tags like <c>, <00:00:00.000>
                    line = re.sub(r"<[^>]+>", "", line)
                    if line:
                        lines.append(line)

                # Deduplicate consecutive lines (VTT often repeats)
                cleaned = []
                prev = None
                for line in lines:
                    if line != prev:
                        cleaned.append(line)
                        prev = line

                transcript = " ".join(cleaned)
                return transcript if transcript else None

            except subprocess.TimeoutExpired:
                logger.warning("yt-dlp subtitle download timed out")
                return None
            except Exception as e:
                logger.warning(f"yt-dlp subtitle parse error: {e}")
                return None

    async def close(self):
        await self.client.aclose()