import json
from dataclasses import dataclass
from pathlib import Path

from local_rag.config import Settings
from local_rag.retrieval import RetrievedChunk, Retriever


@dataclass(frozen=True)
class LabeledQuestion:
    question: str
    doc: str
    sections: tuple[str, ...]


def load_questions(path: Path) -> list[LabeledQuestion]:
    questions = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        questions.append(LabeledQuestion(raw["question"], raw["doc"], tuple(raw["sections"])))
    return questions


def first_relevant_rank(results: list[RetrievedChunk], expected: LabeledQuestion) -> int | None:
    for rank, chunk in enumerate(results, start=1):
        if chunk.doc != expected.doc:
            continue
        section = chunk.section.lower()
        if any(label.lower() in section for label in expected.sections):
            return rank
    return None


def recall_at_k(ranks: list[int | None], k: int) -> float:
    return sum(1 for rank in ranks if rank is not None and rank <= k) / len(ranks)


def mrr(ranks: list[int | None]) -> float:
    return sum(1 / rank for rank in ranks if rank is not None) / len(ranks)


def evaluate(
    retriever: Retriever, questions: list[LabeledQuestion], rerank: bool, limit: int = 10
) -> tuple[dict[str, float], list[dict]]:
    ranks: list[int | None] = []
    misses: list[dict] = []
    for question in questions:
        results = retriever.search(question.question, limit=limit, rerank=rerank)
        rank = first_relevant_rank(results, question)
        ranks.append(rank)
        if rank is None or rank > 3:
            misses.append(
                {
                    "question": question.question,
                    "rank": rank,
                    "top3": [f"{chunk.doc} / {chunk.section}" for chunk in results[:3]],
                }
            )
    metrics = {
        "recall_at_1": recall_at_k(ranks, 1),
        "recall_at_3": recall_at_k(ranks, 3),
        "recall_at_5": recall_at_k(ranks, 5),
        "mrr_at_10": mrr(ranks),
    }
    return metrics, misses


def main() -> None:
    settings = Settings()
    questions = load_questions(settings.eval_dir / "retrieval.jsonl")
    retriever = Retriever(settings)

    hybrid_metrics, hybrid_misses = evaluate(retriever, questions, rerank=False)
    reranked_metrics, reranked_misses = evaluate(retriever, questions, rerank=True)

    print(f"{len(questions)} questions")
    print(f"{'metric':<12} {'hybrid':>8} {'reranked':>9}")
    for key in hybrid_metrics:
        print(f"{key:<12} {hybrid_metrics[key]:>8.3f} {reranked_metrics[key]:>9.3f}")

    results = {
        "questions": len(questions),
        "config": {
            "embedding_model": settings.embedding_model,
            "reranker_model": settings.reranker_model,
            "rerank_candidates": settings.rerank_candidates,
        },
        "hybrid": {"metrics": hybrid_metrics, "misses": hybrid_misses},
        "reranked": {"metrics": reranked_metrics, "misses": reranked_misses},
    }
    results_path = settings.eval_dir / "results" / "retrieval.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Results written to {results_path}")


if __name__ == "__main__":
    main()
