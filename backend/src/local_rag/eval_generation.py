import json
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

from local_rag.config import Settings
from local_rag.generation import GenerationBackend, Message, build_backend
from local_rag.judge import PROMPT_VERSION, Judge
from local_rag.prompting import build_messages, format_excerpts
from local_rag.retrieval import Retriever

ANSWERABLE = ("direct", "paraphrase")
CATEGORIES = ("direct", "paraphrase", "unanswerable")


@dataclass(frozen=True)
class EvalItem:
    id: str
    category: str
    question: str
    expected_facts: tuple[str, ...]


def load_items(path: Path) -> list[EvalItem]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        items.append(
            EvalItem(
                raw["id"], raw["category"], raw["question"], tuple(raw.get("expected_facts", []))
            )
        )
    return items


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    text = "".join(char for char in decomposed if not unicodedata.combining(char))
    text = text.lower().replace("€", " eur")
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    text = re.sub(r"(\d)\s+(\d)", r"\1\2", text)
    text = re.sub(r"\s+%", "%", text)
    return re.sub(r"\s+", " ", text).strip()


def facts_present(facts: tuple[str, ...], answer: str) -> bool:
    haystack = normalize(answer)
    return all(normalize(fact) in haystack for fact in facts)


def extract_citations(answer: str) -> list[int]:
    return [int(number) for number in re.findall(r"\[(\d+)\]", answer)]


def citations_valid(cited: list[int], source_count: int) -> bool:
    return bool(cited) and all(1 <= number <= source_count for number in cited)


def generate(backend: GenerationBackend, messages: list[Message]) -> dict:
    started = time.perf_counter()
    first: float | None = None
    pieces: list[str] = []
    for delta in backend.stream(messages):
        if first is None:
            first = time.perf_counter()
        pieces.append(delta)
    total = time.perf_counter() - started
    first_token = (first - started) if first is not None else total
    generation_time = max(total - first_token, 1e-3)
    return {
        "answer": "".join(pieces),
        "first_token_ms": round(first_token * 1000),
        "total_ms": round(total * 1000),
        "tokens": len(pieces),
        "tokens_per_second": round(len(pieces) / generation_time, 1),
    }


def _rate(values: list[bool]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def aggregate(rows: list[dict]) -> dict[str, dict]:
    categories: dict[str, dict] = {}
    for category in CATEGORIES:
        subset = [row for row in rows if row["category"] == category]
        if not subset:
            continue
        judged = [row for row in subset if row["refusal"] is not None]
        answers = [row for row in judged if row["refusal"] is False]
        answerable = category in ANSWERABLE
        categories[category] = {
            "n": len(subset),
            "judged": len(judged),
            "facts_rate": _rate([row["facts_correct"] for row in subset]) if answerable else None,
            "citation_valid_rate": (
                _rate([row["citation_valid"] for row in subset]) if answerable else None
            ),
            "refusal_rate": _rate([row["refusal"] for row in judged]),
            "supported_rate": _rate(
                [row["supported"] for row in answers if row["supported"] is not None]
            ),
            "median_tokens": median(row["tokens"] for row in subset),
            "median_first_token_ms": median(row["first_token_ms"] for row in subset),
            "mean_tokens_per_second": round(mean(row["tokens_per_second"] for row in subset), 1),
        }
    return categories


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def main() -> None:
    # Greedy decoding keeps eval answers identical between runs, so numbers
    # are stable and cached judge verdicts stay valid. Production sampling
    # settings are unaffected.
    settings = Settings(temperature=0.0, top_p=1.0)
    items = load_items(settings.eval_dir / "generation.jsonl")
    results_dir = settings.eval_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    judge: Judge | None
    try:
        judge = Judge(settings, results_dir / "judge_cache.jsonl")
    except Exception as exc:
        print(f"Judge disabled ({type(exc).__name__}); semantic metrics will be missing.")
        print("Set ANTHROPIC_API_KEY (backend/.env is read) and rerun to fill them in.")
        judge = None

    retriever = Retriever(settings)
    backend = build_backend(settings)

    rows: list[dict] = []
    for index, item in enumerate(items, start=1):
        chunks = retriever.search(item.question)
        messages = build_messages(item.question, chunks)
        generation = generate(backend, messages)
        answer = generation.pop("answer")
        cited = extract_citations(answer)
        row = {
            "id": item.id,
            "category": item.category,
            "question": item.question,
            "answer": answer,
            "citations": cited,
            "facts_correct": facts_present(item.expected_facts, answer),
            "citation_valid": citations_valid(cited, len(chunks)),
            "refusal": None,
            "supported": None,
            "unsupported_claims": [],
            **generation,
        }
        if judge is not None:
            try:
                verdict = judge.evaluate(item.question, format_excerpts(chunks), answer)
                row["refusal"] = verdict.refusal
                row["supported"] = verdict.supported
                row["unsupported_claims"] = verdict.unsupported_claims
            except Exception as exc:
                print(f"Judge disabled after error on {item.id}: {exc}")
                judge = None
        rows.append(row)
        print(
            f"[{index:>2}/{len(items)}] {item.id} {item.category:<12} "
            f"facts={_fmt(row['facts_correct'])} refusal={_fmt(row['refusal'])} "
            f"supported={_fmt(row['supported'])} tokens={row['tokens']}"
        )

    categories = aggregate(rows)
    header = f"{'category':<14}{'n':>4}{'facts':>8}{'cit.ok':>8}{'refusal':>9}{'support':>9}"
    print(header)
    for name, metrics in categories.items():
        print(
            f"{name:<14}{metrics['n']:>4}{_fmt(metrics['facts_rate']):>8}"
            f"{_fmt(metrics['citation_valid_rate']):>8}{_fmt(metrics['refusal_rate']):>9}"
            f"{_fmt(metrics['supported_rate']):>9}"
        )

    judged = any(row["refusal"] is not None for row in rows)
    results = {
        "questions": len(rows),
        "config": {
            "generation_model": settings.generation_model,
            "decoding": "greedy",
            "top_k": settings.top_k,
            "judge_model": settings.judge_model if judged else None,
            "judge_prompt_version": PROMPT_VERSION if judged else None,
        },
        "categories": categories,
        "answers": rows,
    }
    results_path = results_dir / "generation.json"
    results_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Results written to {results_path}")


if __name__ == "__main__":
    main()
