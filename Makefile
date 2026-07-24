.PHONY: setup qdrant qdrant-down corpus ingest search eval-retrieval eval-generation api front front-install lint fmt test

setup:
	cd backend && uv sync

api:
	cd backend && uv run uvicorn --factory local_rag.api:create_app --port 8000

front:
	cd frontend && npm run dev

front-install:
	cd frontend && npm install

qdrant:
	docker compose up -d qdrant

qdrant-down:
	docker compose down

corpus:
	cd backend && uv run python -m local_rag.corpus

ingest:
	cd backend && uv run python -m local_rag.ingest

search:
	cd backend && uv run python -m local_rag.search "$(q)"

eval-retrieval:
	cd backend && uv run python -m local_rag.eval_retrieval

eval-generation:
	cd backend && uv run --group eval python -m local_rag.eval_generation

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

fmt:
	cd backend && uv run ruff format . && uv run ruff check --fix .

test:
	cd backend && uv run pytest
