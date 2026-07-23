import argparse

from local_rag.config import Settings
from local_rag.embedding import Embedder
from local_rag.vectorstore import VectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid search over the indexed corpus")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    settings = Settings()
    embedder = Embedder(settings.embedding_model, settings.device, settings.embed_batch_size)
    dense, sparse = embedder.encode([args.query])
    store = VectorStore(settings.qdrant_url, settings.collection)
    points = store.hybrid_search(dense[0], sparse[0], limit=args.limit)

    if not points:
        print("No result.")
        return
    for rank, point in enumerate(points, start=1):
        payload = point.payload or {}
        pages = ",".join(str(page) for page in payload.get("pages", []))
        header = f"{payload.get('doc')}  p.{pages}  [{payload.get('section')}]"
        print(f"{rank}. score={point.score:.4f}  {header}")
        snippet = " ".join(str(payload.get("text", "")).split())
        print(f"   {snippet[:280]}")


if __name__ == "__main__":
    main()
