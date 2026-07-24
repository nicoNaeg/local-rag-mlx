# local-rag-mlx

> Fully local RAG engine with LoRA fine-tuning, built for Apple Silicon. Hybrid retrieval, cross-encoder reranking, token streaming. No cloud APIs at runtime.

**Status: evaluated end to end.** Ingestion, hybrid retrieval with reranking, streaming serving with its frontend, and the generation evaluation harness are in place; next is LoRA fine-tuning with its before and after table.

## Architecture

- **Ingestion**: PDF to structured text (Docling), structure-aware chunking with page and section metadata
- **Retrieval**: hybrid search (BGE-M3 dense + learned sparse) in Qdrant with server-side RRF fusion, then cross-encoder reranking (bge-reranker-v2-m3)
- **Generation**: Qwen3-8B (4-bit) served in-process with [MLX](https://github.com/ml-explore/mlx), fine-tuned with LoRA for grounded, citation-first answers
- **API and UI**: FastAPI streaming tokens over SSE to a Next.js frontend, with clickable source cards
- **Evaluation**: automated harness measuring retrieval quality and generation faithfulness; the fine-tuning gain is documented with reproducible before/after numbers

Target hardware: Apple M4 Pro, 24 GB unified memory. Everything (embedding, retrieval, reranking, fine-tuning, inference) runs on-device. The generation layer sits behind a backend interface so the same API can target vLLM for datacenter deployment.

## Repository layout

    backend/             FastAPI service and RAG pipeline (Python, uv)
    frontend/            Next.js UI, one page streaming answers with cited sources
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

## Generation quality (baseline)

`make eval-generation` runs the full pipeline (hybrid retrieval, reranking, prompt assembly, generation) on a labeled set of 72 questions (`backend/eval/generation.jsonl`): the 24 direct questions of the retrieval set enriched with expected facts, 24 colloquial paraphrases, and 24 unanswerable questions whose answer exists nowhere in the corpus, where the correct behavior is an explicit refusal. Decoding is greedy during evaluation so numbers are identical from run to run; production sampling is unchanged.

Deterministic metrics are computed locally: expected facts present in the answer (after normalizing accents, currency and number formats), citation validity (every `[n]` marker points at a provided excerpt), concision and latency. Two semantic metrics are delegated to an LLM judge (`claude-opus-4-8`, strict structured output): refusal classification, and citation support, meaning every claim is backed by the excerpt it cites. Verdicts are cached in `backend/eval/results/judge_cache.jsonl` and committed, so a rerun with unchanged answers rebuilds the table without any API call. The judge is an evaluation tool only; the serving runtime stays fully local.

Baseline of the base model (Qwen3-8B 4-bit, before fine-tuning):

| metric | direct | paraphrase | unanswerable |
|--------|--------|------------|--------------|
| expected facts present | 0.958 | 0.917 | |
| citation validity | 1.000 | 1.000 | |
| median answer tokens | 30 | 33 | 27 |

The judged metrics (refusal rate on the unanswerable set, per-claim citation support) complete this table once the judge pass runs; they are the primary targets of the milestone 5 before and after comparison. The three failures on answerable questions are instructive: one answer inverts a security instruction (keep the compromised machine connected, where the policy says the opposite), one invents a reimbursement rule by conflating two adjacent policies, one returns half of a two-part fact. All three carry well-formed citations, which is why citation validity alone is not a faithfulness metric and the fine-tuning targets grounding rather than formatting.

## Serving

`make api` starts FastAPI on port 8000. `make front` starts the Next.js UI on http://localhost:3000 and proxies API calls to the backend, so the demo lives entirely at that address.

The generation endpoint is `POST /api/query` with `{"question": "..."}`, answered as a single SSE stream: a `sources` event as soon as hybrid search and reranking finish (the UI renders source cards while the model runs), one `token` event per decoded token, then `done` carrying latency metrics (retrieval, first token, tokens per second). Generation failures arrive as an `error` event rather than a broken stream. `GET /healthz` reports Qdrant reachability and the loaded backend.

A single Metal GPU runs one generation at a time, so requests pass through a bounded async queue consumed by one worker; when the queue is full the API answers 503 with Retry-After instead of stacking latency, and a client disconnect cancels the in-flight generation.

Generation runs in-process with MLX (Qwen3-8B, 4-bit) behind a small backend protocol. Setting `RAG_GENERATION_BACKEND=openai` points the same API at any OpenAI-compatible server (vLLM, TGI) via `RAG_OPENAI_BASE_URL`: the local demo and a datacenter deployment share the serving layer. Qwen3's thinking mode is off by default to keep first-token latency low; set `RAG_THINKING=true` to compare.

## Getting started

Requires [uv](https://docs.astral.sh/uv/), Docker, and Node 20+.

    make setup       install backend dependencies
    make qdrant      start Qdrant in Docker
    make corpus      generate the demo corpus PDFs into data/corpus
    make ingest      extract, chunk, embed and index the corpus
    make search q="votre question"   hybrid search + rerank over the index
    make eval-retrieval   measure retrieval quality on the labeled set
    make eval-generation   measure generation quality (LLM judge needs ANTHROPIC_API_KEY)
    make api         start the API server (loads the models, port 8000)
    make front-install   install frontend dependencies
    make front       start the frontend on http://localhost:3000
    make lint        ruff check + format check
    make test        run the test suite
