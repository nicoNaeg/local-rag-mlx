import asyncio
import json
import threading
from collections.abc import Iterator

import httpx
import pytest

from local_rag.api import create_app, sse_event
from local_rag.config import Settings
from local_rag.generation import Message
from local_rag.retrieval import RetrievedChunk

pytestmark = pytest.mark.anyio

CHUNKS = [
    RetrievedChunk(doc="frais", section="Plafonds", pages=(1,), text="22 EUR.", score=0.95),
    RetrievedChunk(doc="rh", section="Conges", pages=(2,), text="25 jours.", score=0.10),
]


class FakeRetriever:
    def search(self, query: str, limit: int | None = None, rerank: bool = True):
        return CHUNKS

    def ping(self) -> bool:
        return True


class FakeBackend:
    def stream(self, messages: list[Message]) -> Iterator[str]:
        yield "Le plafond "
        yield "est 22 EUR [1]."


class FailingBackend:
    def stream(self, messages: list[Message]) -> Iterator[str]:
        message = "model exploded"
        raise RuntimeError(message)
        yield ""


class BlockingBackend:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()

    def stream(self, messages: list[Message]) -> Iterator[str]:
        self.started.set()
        self.release.wait(timeout=5)
        yield "late"


def parse_sse(body: str) -> list[tuple[str, object]]:
    events = []
    for block in body.split("\n\n"):
        name, data = None, None
        for line in block.split("\n"):
            if line.startswith("event: "):
                name = line.removeprefix("event: ")
            elif line.startswith("data: "):
                data = json.loads(line.removeprefix("data: "))
        if name is not None:
            events.append((name, data))
    return events


def make_client(backend, queue_size: int = 8):
    app = create_app(
        settings=Settings(queue_size=queue_size),
        retriever=FakeRetriever(),
        backend=backend,
    )
    return app, app.router.lifespan_context(app)


async def test_query_streams_sources_tokens_done() -> None:
    app, lifespan = make_client(FakeBackend())
    async with lifespan:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/query", json={"question": "Plafond repas ?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert names[0] == "sources"
    assert names[-1] == "done"

    sources = events[0][1]
    assert [source["id"] for source in sources] == [1, 2]
    assert sources[0]["doc"] == "frais"
    assert sources[0]["text"] == "22 EUR."

    answer = "".join(data["text"] for name, data in events if name == "token")
    assert answer == "Le plafond est 22 EUR [1]."

    done = events[-1][1]
    assert done["tokens"] == 2
    assert {"retrieval_ms", "first_token_ms", "total_ms", "tokens_per_second"} <= set(done)


async def test_generation_error_is_reported_as_event() -> None:
    app, lifespan = make_client(FailingBackend())
    async with lifespan:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/query", json={"question": "Plafond ?"})

    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert "error" in names
    assert "done" not in names
    error = dict(events)["error"]
    assert "model exploded" in error["message"]


async def test_full_queue_returns_503() -> None:
    backend = BlockingBackend()
    app, lifespan = make_client(backend, queue_size=1)
    payload = {"question": "Plafond ?"}
    async with lifespan:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            running = asyncio.create_task(client.post("/api/query", json=payload))
            assert await asyncio.to_thread(backend.started.wait, 5)

            queued = asyncio.create_task(client.post("/api/query", json=payload))
            for _ in range(100):
                if app.state.jobs.full():
                    break
                await asyncio.sleep(0.02)
            assert app.state.jobs.full()

            rejected = await client.post("/api/query", json=payload)
            assert rejected.status_code == 503
            assert rejected.headers["retry-after"] == "5"

            backend.release.set()
            assert (await running).status_code == 200
            assert (await queued).status_code == 200


async def test_healthz_reports_backend_and_qdrant() -> None:
    app, lifespan = make_client(FakeBackend())
    async with lifespan:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/healthz")

    body = response.json()
    assert body["status"] == "ok"
    assert body["qdrant"] is True
    assert body["backend"] == "FakeBackend"


async def test_empty_question_is_rejected() -> None:
    app, lifespan = make_client(FakeBackend())
    async with lifespan:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/query", json={"question": ""})

    assert response.status_code == 422


def test_sse_event_is_single_line() -> None:
    event = sse_event("token", {"text": "line one\nline two"})

    assert event == 'event: token\ndata: {"text": "line one\\nline two"}\n\n'
    assert event.count("\n\n") == 1
