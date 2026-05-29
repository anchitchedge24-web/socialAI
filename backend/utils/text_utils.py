import re
from typing import List


def clean_transcript(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"♪.*?♪", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s.,!?;:'\"-]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_hashtags(text: str) -> List[str]:
    if not text:
        return []
    return re.findall(r"#(\w+)", text)


def truncate_text(text: str, max_length: int = 500) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."