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

## Getting started

Requires [uv](https://docs.astral.sh/uv/), Docker, and Node 20+ (frontend, later).

    make setup       install backend dependencies
    make qdrant      start Qdrant in Docker
    make lint        ruff check + format check
    make test        run the test suite
