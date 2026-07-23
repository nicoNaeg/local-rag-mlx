import time

from local_rag.chunking import chunk_blocks
from local_rag.config import Settings
from local_rag.embedding import Embedder
from local_rag.extraction import extract_blocks
from local_rag.vectorstore import VectorStore


def main() -> None:
    settings = Settings()
    pdfs = sorted(settings.corpus_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDF found in {settings.corpus_dir}. Run 'make corpus' first.")

    started = time.perf_counter()
    chunks = []
    for pdf in pdfs:
        doc_chunks = chunk_blocks(pdf.stem, extract_blocks(pdf))
        chunks.extend(doc_chunks)
        print(f"{pdf.name}: {len(doc_chunks)} chunks")

    texts = [f"{chunk.doc} | {chunk.section}\n{chunk.text}" for chunk in chunks]
    embedder = Embedder(settings.embedding_model, settings.device, settings.embed_batch_size)
    dense, sparse = embedder.encode(texts)

    store = VectorStore(settings.qdrant_url, settings.collection)
    store.recreate(dense_dim=len(dense[0]))
    store.upsert(chunks, dense, sparse)

    elapsed = time.perf_counter() - started
    print(
        f"Indexed {len(chunks)} chunks from {len(pdfs)} documents "
        f"into '{settings.collection}' in {elapsed:.1f}s"
    )


if __name__ == "__main__":
    main()
