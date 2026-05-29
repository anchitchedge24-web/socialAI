import logging
from typing import List
from models.chunk_models import TextChunk
from models.video_metadata import VideoMetadata
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TranscriptChunker:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_transcript(self, metadata: VideoMetadata) -> List[TextChunk]:
        if not metadata.transcript:
            logger.warning(f"No transcript for video {metadata.video_id}")
            return []

        text = metadata.transcript
        words = text.split()
        chunks = []

        if len(words) <= self.chunk_size:
            chunk = TextChunk(
                chunk_id=f"{metadata.video_id}_chunk_0",
                video_id=metadata.video_id,
                text=text,
                creator_name=metadata.creator_name,
                source_platform=metadata.platform,
                timestamp_start=0.0,
                timestamp_end=metadata.duration,
                chunk_index=0,
                total_chunks=1,
            )
            return [chunk]

        start = 0
        chunk_index = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_text = " ".join(words[start:end])

            duration = metadata.duration or 60.0
            total_words = len(words)
            ts_start = (start / total_words) * duration if total_words > 0 else 0
            ts_end = (end / total_words) * duration if total_words > 0 else 0

            chunk = TextChunk(
                chunk_id=f"{metadata.video_id}_chunk_{chunk_index}",
                video_id=metadata.video_id,
                text=chunk_text,
                creator_name=metadata.creator_name,
                source_platform=metadata.platform,
                timestamp_start=round(ts_start, 2),
                timestamp_end=round(ts_end, 2),
                chunk_index=chunk_index,
                total_chunks=0,
            )
            chunks.append(chunk)
            chunk_index += 1

            step = self.chunk_size - self.chunk_overlap
            if step <= 0:
                step = self.chunk_size
            start += step

        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        logger.info(f"Created {len(chunks)} chunks for video {metadata.video_id}")
        return chunks

    def chunk_both_videos(self, video_a: VideoMetadata, video_b: VideoMetadata) -> List[TextChunk]:
        chunks_a = self.chunk_transcript(video_a)
        chunks_b = self.chunk_transcript(video_b)
        return chunks_a + chunks_b