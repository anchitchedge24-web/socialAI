import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from config.settings import get_settings
from models.chunk_models import TextChunk
from rag.embedder import EmbeddingService

logger = logging.getLogger(__name__)
settings = get_settings()


class ChromaStore:
    _instance = None
    _client = None
    _collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if ChromaStore._client is None:
            logger.info(f"Initializing ChromaDB at: {settings.CHROMA_PERSIST_DIR}")
            ChromaStore._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            ChromaStore._collection = ChromaStore._client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB collection '{settings.CHROMA_COLLECTION_NAME}' ready")

    @property
    def collection(self):
        return ChromaStore._collection

    def clear_collection(self):
        try:
            ChromaStore._client.delete_collection(settings.CHROMA_COLLECTION_NAME)
            ChromaStore._collection = ChromaStore._client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Collection cleared and recreated")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")

    def add_chunks(self, chunks: List[TextChunk], embeddings: List[List[float]]):
        if not chunks or not embeddings:
            logger.warning("No chunks or embeddings to add")
            return

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "video_id": chunk.video_id,
                "creator_name": chunk.creator_name,
                "source_platform": chunk.source_platform,
                "timestamp_start": chunk.timestamp_start or 0.0,
                "timestamp_end": chunk.timestamp_end or 0.0,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
            }
            for chunk in chunks
        ]

        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_embeds = embeddings[i:i + batch_size]

            self.collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas,
                embeddings=batch_embeds,
            )

        logger.info(f"Added {len(chunks)} chunks to ChromaDB")

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            kwargs = {
                "query_embeddings": query_embeddings,
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                kwargs["where"] = where

            results = self.collection.query(**kwargs)
            return results
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    def get_count(self) -> int:
        return self.collection.count()