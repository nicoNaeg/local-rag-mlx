import hashlib
import json
from pathlib import Path

from pydantic import BaseModel

from local_rag.config import Settings

PROMPT_VERSION = "1"

JUDGE_SYSTEM = (
    "You grade the answer of a retrieval-augmented assistant over internal company documents. "
    "You receive a question, the numbered excerpts the assistant saw, and its answer. "
    "Set refusal to true when the answer declines because the excerpts do not contain the "
    "information, false when it provides an answer. "
    "For an answer, set supported to true only if every factual claim is directly backed by the "
    "excerpt it cites; set it to false if any claim is missing from the cited excerpts, "
    "contradicts them, or cites the wrong excerpt. For a refusal, set supported to null. "
    "Copy each unsupported claim into unsupported_claims, empty when there are none."
)


class Verdict(BaseModel):
    refusal: bool
    supported: bool | None
    unsupported_claims: list[str]


def cache_key(model: str, question: str, answer: str) -> str:
    material = "\n".join([model, PROMPT_VERSION, question, answer])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class JudgeCache:
    """Append-only verdict store committed to the repo, so a rerun with
    unchanged answers reproduces the table without any API call."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._verdicts: dict[str, Verdict] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    raw = json.loads(line)
                    self._verdicts[raw["key"]] = Verdict(**raw["verdict"])

    def get(self, key: str) -> Verdict | None:
        return self._verdicts.get(key)

    def put(self, key: str, verdict: Verdict) -> None:
        self._verdicts[key] = verdict
        with self._path.open("a", encoding="utf-8") as handle:
            record = {"key": key, "verdict": verdict.model_dump()}
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


class Judge:
    def __init__(self, settings: Settings, cache_path: Path) -> None:
        # Imported here because the eval dependency group and API credentials
        # are only needed when judging actually runs.
        import anthropic
        from dotenv import load_dotenv

        load_dotenv()
        self._client = anthropic.Anthropic()
        self._model = settings.judge_model
        self._cache = JudgeCache(cache_path)
        # count_tokens is free and fails fast when credentials are missing.
        self._client.messages.count_tokens(
            model=self._model, messages=[{"role": "user", "content": "ping"}]
        )

    def evaluate(self, question: str, excerpts: str, answer: str) -> Verdict:
        key = cache_key(self._model, question, answer)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        response = self._client.messages.parse(
            model=self._model,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=JUDGE_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Question:\n{question}\n\nExcerpts:\n{excerpts}\n\nAnswer:\n{answer}"
                    ),
                }
            ],
            output_format=Verdict,
        )
        verdict = response.parsed_output
        if verdict is None:
            raise RuntimeError(f"judge returned no parseable verdict for: {question}")
        self._cache.put(key, verdict)
        return verdict
