import argparse

from local_rag.config import Settings
from local_rag.retrieval import Retriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid search with cross-encoder reranking")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--no-rerank", action="store_true")
    args = parser.parse_args()

    retriever = Retriever(Settings())
    chunks = retriever.search(args.query, limit=args.limit, rerank=not args.no_rerank)

    if not chunks:
        print("No result.")
        return
    for rank, chunk in enumerate(chunks, start=1):
        pages = ",".join(str(page) for page in chunk.pages)
        print(f"{rank}. score={chunk.score:.4f}  {chunk.doc}  p.{pages}  [{chunk.section}]")
        snippet = " ".join(chunk.text.split())
        print(f"   {snippet[:280]}")


if __name__ == "__main__":
    main()
