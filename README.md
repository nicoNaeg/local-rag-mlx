# local-rag-mlx

> Fully local RAG engine with LoRA fine-tuning on Apple Silicon (MLX) — hybrid retrieval, cross-encoder reranking, token streaming. No cloud APIs at runtime.

**Status: 🚧 design phase** — architecture decisions are being discussed and recorded before code lands.

## Planned architecture

- **Ingestion**: PDF → structured text → chunking with page/section metadata
- **Retrieval**: hybrid search (dense + sparse) in a local vector store, then cross-encoder reranking
- **Generation**: 7–9B instruct model served in-process with [MLX](https://github.com/ml-explore/mlx), fine-tuned with LoRA for grounded, citation-first answers
- **API/UI**: FastAPI streaming tokens over SSE to a web frontend, with clickable source cards
- **Evaluation**: automated harness measuring retrieval quality and generation faithfulness — the fine-tuning gain will be documented with reproducible before/after numbers

Target hardware: Apple M4 Pro, 24 GB unified memory. Everything — embedding, retrieval, reranking, fine-tuning, inference — runs on-device.
