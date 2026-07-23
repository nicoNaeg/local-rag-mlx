.PHONY: setup qdrant qdrant-down lint fmt test

setup:
	cd backend && uv sync

qdrant:
	docker compose up -d qdrant

qdrant-down:
	docker compose down

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

fmt:
	cd backend && uv run ruff format . && uv run ruff check --fix .

test:
	cd backend && uv run pytest
