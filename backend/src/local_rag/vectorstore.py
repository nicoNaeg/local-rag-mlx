from uuid import uuid4

from qdrant_client import QdrantClient, models

from local_rag.chunking import Chunk


class VectorStore:
    def __init__(self, url: str, collection: str) -> None:
        self._client = QdrantClient(url=url)
        self._collection = collection

    def recreate(self, dense_dim: int) -> None:
        if self._client.collection_exists(self._collection):
            self._client.delete_collection(self._collection)
        self._client.create_collection(
            self._collection,
            vectors_config={
                "dense": models.VectorParams(size=dense_dim, distance=models.Distance.COSINE)
            },
            sparse_vectors_config={"sparse": models.SparseVectorParams()},
        )

    def upsert(
        self,
        chunks: list[Chunk],
        dense: list[list[float]],
        sparse: list[dict[int, float]],
        batch_size: int = 64,
    ) -> None:
        points = [
            models.PointStruct(
                id=str(uuid4()),
                vector={
                    "dense": vector,
                    "sparse": models.SparseVector(
                        indices=list(weights), values=list(weights.values())
                    ),
                },
                payload={
                    "doc": chunk.doc,
                    "section": chunk.section,
                    "pages": list(chunk.pages),
                    "text": chunk.text,
                },
            )
            for chunk, vector, weights in zip(chunks, dense, sparse, strict=True)
        ]
        for start in range(0, len(points), batch_size):
            self._client.upsert(self._collection, points=points[start : start + batch_size])

    def hybrid_search(
        self,
        dense: list[float],
        sparse: dict[int, float],
        limit: int = 10,
        prefetch: int = 20,
    ) -> list[models.ScoredPoint]:
        result = self._client.query_points(
            self._collection,
            prefetch=[
                models.Prefetch(query=dense, using="dense", limit=prefetch),
                models.Prefetch(
                    query=models.SparseVector(indices=list(sparse), values=list(sparse.values())),
                    using="sparse",
                    limit=prefetch,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True,
        )
        return result.points
