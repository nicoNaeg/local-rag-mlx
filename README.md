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

## Retrieval quality

Retrieval is measured on a labeled set of 24 questions over the demo corpus (`backend/eval/retrieval.jsonl`), each mapped to the document and section holding the answer. `make eval-retrieval` reruns the measurement and rewrites `backend/eval/results/retrieval.json`; the candidate pool is identical in both configurations, so the delta isolates what the cross-encoder adds.

| metric | hybrid | hybrid + reranker |
|--------|--------|-------------------|
| recall@1 | 0.917 | 1.000 |
| recall@3 | 1.000 | 1.000 |
| recall@5 | 1.000 | 1.000 |
| MRR@10 | 0.951 | 1.000 |

Hybrid search alone already places a relevant chunk in the top 3 for every question; the reranker fixes the remaining rank-1 misses, which matters because only the top 3 to 5 chunks enter the prompt. These numbers are a ceiling: the corpus is clean and the questions direct. The generation evaluation (milestone 4) adds paraphrased and unanswerable questions that stress the pipeline harder.

## Getting started

Requires [uv](https://docs.astral.sh/uv/), Docker, and Node 20+ (frontend, later).

    make setup       install backend dependencies
    make qdrant      start Qdrant in Docker
    make corpus      generate the demo corpus PDFs into data/corpus
    make ingest      extract, chunk, embed and index the corpus
    make search q="votre question"   hybrid search + rerank over the index
    make eval-retrieval   measure retrieval quality on the labeled set
    make lint        ruff check + format check
    make test        run the test suite
