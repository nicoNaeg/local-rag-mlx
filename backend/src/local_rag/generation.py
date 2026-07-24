import json
from collections.abc import Iterator
from typing import Protocol

from local_rag.config import Settings

Message = dict[str, str]


class GenerationBackend(Protocol):
    def stream(self, messages: list[Message]) -> Iterator[str]:
        """Yield completion text deltas for a chat conversation."""
        ...


class MLXBackend:
    def __init__(self, settings: Settings) -> None:
        # Imported here because mlx must not load for commands that never
        # generate.
        from mlx_lm import load, stream_generate
        from mlx_lm.sample_utils import make_sampler

        self._stream_generate = stream_generate
        self._model, self._tokenizer = load(settings.generation_model)
        self._sampler = make_sampler(temp=settings.temperature, top_p=settings.top_p)
        self._max_tokens = settings.max_tokens
        self._thinking = settings.thinking

    def stream(self, messages: list[Message]) -> Iterator[str]:
        prompt = self._tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, enable_thinking=self._thinking
        )
        for response in self._stream_generate(
            self._model,
            self._tokenizer,
            prompt,
            max_tokens=self._max_tokens,
            sampler=self._sampler,
        ):
            yield response.text


class OpenAICompatBackend:
    """Scale-out path: same contract against vLLM or TGI.

    Selected with RAG_GENERATION_BACKEND=openai; the API layer is unchanged.
    """

    def __init__(self, settings: Settings) -> None:
        import httpx

        self._client = httpx.Client(
            base_url=settings.openai_base_url,
            timeout=httpx.Timeout(10.0, read=300.0),
        )
        self._body = {
            "model": settings.generation_model,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "stream": True,
        }

    def stream(self, messages: list[Message]) -> Iterator[str]:
        body = {**self._body, "messages": messages}
        with self._client.stream("POST", "/chat/completions", json=body) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line.removeprefix("data: ")
                if payload == "[DONE]":
                    break
                choices = json.loads(payload).get("choices") or []
                delta = choices[0].get("delta", {}).get("content") if choices else None
                if delta:
                    yield delta


def build_backend(settings: Settings) -> GenerationBackend:
    if settings.generation_backend == "openai":
        return OpenAICompatBackend(settings)
    return MLXBackend(settings)
