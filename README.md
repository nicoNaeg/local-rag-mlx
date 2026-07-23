# local-rag-mlx

> Fully local RAG engine with LoRA fine-tuning, built for Apple Silicon. Hybrid retrieval, cross-encoder reranking, token streaming. No cloud APIs at runtime.

**Status: early development.** Architecture is settled and recorded; the pipeline is being built milestone by milestone.

## Architecture

- **Ingestion**: PDF to structured text (Docling), structure-aware chunking with page and section metadata
- **Retrieval**: hybrid search (BGE-M3 dense + learned sparse) in Qdrant with server-side RRF fusion, then cross-encoder reranking (bge-reranker-v2-m3)
- **Generation**: Qwen3-8B (4-bit) served in-process with [MLX](https://github.com/ml-explore/mlx), fine-tuned with LoRA for grounded, citation-first answers
- **API and UI**: FastAPI streaming tokens over SSE to a Next.js frontend, with clickable source cards
- **Evaluation**: automated harness measuring retrieval quality and generation faithfulness; the fine-tuning gain is documented with reproducible before/after numbers

Target hardware: Apple M4 Pro, 24 GB unified memory. Everything (embedding, retrieval, reranking, fine-tuning, inference) runs on-device. The generation layer sits behind a backend interface so the same API can target vLLM for datacenter deployment.

## Repository layout

    backend/             FastAPI service and RAG pipeline (Python, uv)
    frontend/            Next.js UI (arrives with milestone 3)
    docker-compose.yml   Local Qdrant
    data/                Corpus and working data (gitignored)

## Demo corpus

The demo corpus is a set of internal documents from Solencia, a fictional French renewable-energy company: HR manual, security policy, onboarding guide, expense procedure, purchasing procedure and the technical spec of its product. They are generated locally as real PDFs so the full extraction pipeline runs on realistic input, and they are dense in precise facts (amounts, thresholds, deadlines) that later serve as ground truth for evaluation. Drop your own PDFs into `data/corpus/` to index them as well.

## Getting started

Requires [uv](https://docs.astral.sh/uv/), Docker, and Node 20+ (frontend, later).

    make setup       install backend dependencies
    make qdrant      start Qdrant in Docker
    make corpus      generate the demo corpus PDFs into data/corpus
    make ingest      extract, chunk, embed and index the corpus
    make search q="votre question"   hybrid search over the index
    make lint        ruff check + format check
    make test        run the test suite
