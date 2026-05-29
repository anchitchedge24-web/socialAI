import re
from typing import Optional


def validate_youtube_url(url: str) -> bool:
    patterns = [
        r"(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+",
        r"(https?://)?(www\.)?youtu\.be/[\w-]+",
        r"(https?://)?(www\.)?youtube\.com/shorts/[\w-]+",
    ]
    return any(re.match(p, url) for p in patterns)


def validate_instagram_url(url: str) -> bool:
    patterns = [
        r"(https?://)?(www\.)?instagram\.com/reel/[\w-]+",
        r"(https?://)?(www\.)?instagram\.com/reels/[\w-]+",
        r"(https?://)?(www\.)?instagram\.com/p/[\w-]+",
        r"(https?://)?(www\.)?instagram\.com/tv/[\w-]+",
    ]
    return any(re.match(p, url) for p in patterns)


def extract_youtube_id(url: str) -> Optional[str]:
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_instagram_shortcode(url: str) -> Optional[str]:
    patterns = [
        r"instagram\.com/(?:reel|reels|p|tv)/([\w-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None