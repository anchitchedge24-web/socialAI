import logging
from typing import List, Dict, Any, Optional
from vectorstore.chroma_store import ChromaStore
from rag.embedder import EmbeddingService
from models.chat_models import SourceCitation

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self):
        self.chroma = ChromaStore()
        self.embedder = EmbeddingService()

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        video_id_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query_embedding = self.embedder.embed_query(query)

        where_filter = None
        if video_id_filter:
            where_filter = {"video_id": video_id_filter}

        results = self.chroma.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
        )

        retrieved = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

            for doc, meta, dist, doc_id in zip(docs, metadatas, distances, ids):
                relevance = max(0, 1 - dist)
                retrieved.append({
                    "text": doc,
                    "metadata": meta,
                    "relevance_score": round(relevance, 4),
                    "chunk_id": doc_id,
                    "video_id": meta.get("video_id", ""),
                })

        return retrieved

    def retrieve_as_citations(
        self,
        query: str,
        n_results: int = 5,
        video_id_filter: Optional[str] = None,
    ) -> List[SourceCitation]:
        results = self.retrieve(query, n_results, video_id_filter)
        citations = []
        for r in results:
            citation = SourceCitation(
                video_id=r.get("video_id", ""),
                chunk_id=r.get("chunk_id", ""),
                text_snippet=r.get("text", "")[:200],
                relevance_score=r.get("relevance_score", 0.0),
                timestamp_start=r.get("metadata", {}).get("timestamp_start"),
                timestamp_end=r.get("metadata", {}).get("timestamp_end"),
            )
            citations.append(citation)
        return citations