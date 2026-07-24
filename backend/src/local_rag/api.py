import asyncio
import json
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from local_rag.config import Settings
from local_rag.generation import GenerationBackend, Message, build_backend
from local_rag.prompting import build_messages
from local_rag.retrieval import RetrievedChunk, Retriever

KEEPALIVE_SECONDS = 15.0


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@dataclass
class Job:
    messages: list[Message]
    deltas: asyncio.Queue[str | None] = field(default_factory=asyncio.Queue)
    error: str | None = None
    cancelled: bool = False


def sse_event(event: str, data: object) -> str:
    # json.dumps keeps the payload on one line, as the SSE data field requires.
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _run_generation(backend: GenerationBackend, job: Job, loop: asyncio.AbstractEventLoop) -> None:
    try:
        for delta in backend.stream(job.messages):
            if job.cancelled:
                break
            loop.call_soon_threadsafe(job.deltas.put_nowait, delta)
    except Exception as exc:
        job.error = str(exc)
    finally:
        loop.call_soon_threadsafe(job.deltas.put_nowait, None)


async def _worker(jobs: asyncio.Queue[Job], backend: GenerationBackend) -> None:
    # Single consumer: the one Metal GPU runs one generation at a time.
    loop = asyncio.get_running_loop()
    while True:
        job = await jobs.get()
        if not job.cancelled:
            await asyncio.to_thread(_run_generation, backend, job, loop)
        jobs.task_done()


def _load_retriever(settings: Settings) -> Retriever:
    retriever = Retriever(settings)
    # One dry-run search loads the reranker and checks Qdrant, so startup
    # fails fast instead of the first request.
    retriever.search("warmup", limit=1)
    return retriever


def _source(number: int, chunk: RetrievedChunk) -> dict[str, object]:
    return {
        "id": number,
        "doc": chunk.doc,
        "section": chunk.section,
        "pages": list(chunk.pages),
        "score": round(chunk.score, 4),
        "text": chunk.text,
    }


def _busy() -> JSONResponse:
    return JSONResponse(
        {"detail": "generation queue is full, retry shortly"},
        status_code=503,
        headers={"Retry-After": "5"},
    )


async def _stream(job: Job, chunks: list[RetrievedChunk], retrieval_ms: float):
    try:
        yield sse_event("sources", [_source(n, chunk) for n, chunk in enumerate(chunks, start=1)])
        started = time.perf_counter()
        first_token_ms: float | None = None
        tokens = 0
        while True:
            try:
                delta = await asyncio.wait_for(job.deltas.get(), timeout=KEEPALIVE_SECONDS)
            except TimeoutError:
                yield ": keep-alive\n\n"
                continue
            if delta is None:
                break
            if first_token_ms is None:
                first_token_ms = (time.perf_counter() - started) * 1000
            tokens += 1
            yield sse_event("token", {"text": delta})
        if job.error is not None:
            yield sse_event("error", {"message": job.error})
            return
        total_ms = (time.perf_counter() - started) * 1000
        generation_s = max(total_ms - (first_token_ms or 0.0), 1.0) / 1000
        yield sse_event(
            "done",
            {
                "retrieval_ms": round(retrieval_ms),
                "first_token_ms": round(first_token_ms or 0),
                "total_ms": round(total_ms),
                "tokens": tokens,
                "tokens_per_second": round(tokens / generation_s, 1),
            },
        )
    finally:
        # Stops the generation thread early when the client disconnects.
        job.cancelled = True


def create_app(
    settings: Settings | None = None,
    retriever: Retriever | None = None,
    backend: GenerationBackend | None = None,
) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.retriever = retriever or await asyncio.to_thread(_load_retriever, settings)
        app.state.backend = backend or await asyncio.to_thread(build_backend, settings)
        app.state.jobs = asyncio.Queue(maxsize=settings.queue_size)
        worker = asyncio.create_task(_worker(app.state.jobs, app.state.backend))
        yield
        worker.cancel()

    app = FastAPI(title="local-rag-mlx", lifespan=lifespan)

    @app.get("/healthz")
    async def healthz() -> dict[str, object]:
        qdrant_up = await asyncio.to_thread(app.state.retriever.ping)
        return {
            "status": "ok" if qdrant_up else "degraded",
            "qdrant": qdrant_up,
            "backend": type(app.state.backend).__name__,
            "model": settings.generation_model,
        }

    @app.post("/api/query")
    async def query(request: QueryRequest):
        jobs: asyncio.Queue[Job] = app.state.jobs
        if jobs.full():
            return _busy()
        started = time.perf_counter()
        chunks = await asyncio.to_thread(app.state.retriever.search, request.question)
        retrieval_ms = (time.perf_counter() - started) * 1000
        job = Job(messages=build_messages(request.question, chunks))
        try:
            jobs.put_nowait(job)
        except asyncio.QueueFull:
            return _busy()
        return StreamingResponse(
            _stream(job, chunks, retrieval_ms),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app
