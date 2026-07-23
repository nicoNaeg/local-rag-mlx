from dataclasses import dataclass, replace

from local_rag.config import Settings
from local_rag.embedding import Embedder
from local_rag.reranking import Reranker
from local_rag.vectorstore import VectorStore


@dataclass(frozen=True)
class RetrievedChunk:
    doc: str
    section: str
    pages: tuple[int, ...]
    text: str
    score: float


class Retriever:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._embedder = Embedder(
            settings.embedding_model, settings.device, settings.embed_batch_size
        )
        self._store = VectorStore(settings.qdrant_url, settings.collection)
        self._reranker: Reranker | None = None

    def search(
        self, query: str, limit: int | None = None, rerank: bool = True
    ) -> list[RetrievedChunk]:
        limit = limit or self._settings.top_k
        dense, sparse = self._embedder.encode([query])
        points = self._store.hybrid_search(
            dense[0],
            sparse[0],
            limit=self._settings.rerank_candidates,
            prefetch=self._settings.rerank_candidates,
        )
        chunks = [
            RetrievedChunk(
                doc=str(point.payload.get("doc", "")),
                section=str(point.payload.get("section", "")),
                pages=tuple(point.payload.get("pages", [])),
                text=str(point.payload.get("text", "")),
                score=float(point.score),
            )
            for point in points
            if point.payload
        ]
        if rerank and chunks:
            passages = [f"{chunk.section}\n{chunk.text}" for chunk in chunks]
            scores = self._get_reranker().score(query, passages)
            order = sorted(range(len(chunks)), key=lambda index: scores[index], reverse=True)
            chunks = [replace(chunks[index], score=scores[index]) for index in order]
        return chunks[:limit]

    def _get_reranker(self) -> Reranker:
        if self._reranker is None:
            self._reranker = Reranker(self._settings.reranker_model, self._settings.device)
        return self._reranker
