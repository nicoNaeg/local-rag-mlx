from pathlib import Path

from local_rag.eval_generation import (
    aggregate,
    citations_valid,
    extract_citations,
    facts_present,
    load_items,
    normalize,
)
from local_rag.judge import JudgeCache, Verdict, cache_key


def row(category: str, facts: bool, valid: bool, refusal: bool | None, supported: bool | None):
    return {
        "category": category,
        "facts_correct": facts,
        "citation_valid": valid,
        "refusal": refusal,
        "supported": supported,
        "tokens": 40,
        "first_token_ms": 2000,
        "tokens_per_second": 50.0,
    }


def test_normalize_handles_french_variants() -> None:
    assert normalize("22 €") == "22 eur"
    assert normalize("1 800 EUR") == "1800 eur"
    assert normalize("0,52 EUR") == "0.52 eur"
    assert normalize("99,5 %") == "99.5%"
    assert normalize("16 caractères") == "16 caracteres"


def test_facts_present_matches_reworded_answers() -> None:
    answer = "Le plafond est de 22 euros par repas [1]."
    assert facts_present(("22 EUR",), answer)
    assert not facts_present(("38 EUR",), answer)
    assert facts_present((), answer)
    assert facts_present(("1 800 EUR",), "Le budget est de 1800 EUR par an [2].")


def test_citations_extraction_and_validity() -> None:
    assert extract_citations("Voir [1] et [3].") == [1, 3]
    assert extract_citations("Aucune citation ici.") == []
    assert citations_valid([1, 3], 5)
    assert not citations_valid([6], 5)
    assert not citations_valid([], 5)


def test_aggregate_by_category() -> None:
    rows = [
        row("direct", facts=True, valid=True, refusal=False, supported=True),
        row("direct", facts=False, valid=True, refusal=False, supported=False),
        row("unanswerable", facts=True, valid=False, refusal=True, supported=None),
        row("unanswerable", facts=True, valid=False, refusal=None, supported=None),
    ]

    categories = aggregate(rows)

    assert categories["direct"]["facts_rate"] == 0.5
    assert categories["direct"]["citation_valid_rate"] == 1.0
    assert categories["direct"]["supported_rate"] == 0.5
    assert categories["unanswerable"]["facts_rate"] is None
    assert categories["unanswerable"]["refusal_rate"] == 1.0
    assert categories["unanswerable"]["judged"] == 1


def test_load_items(tmp_path: Path) -> None:
    path = tmp_path / "set.jsonl"
    path.write_text(
        '{"id": "d01", "category": "direct", "question": "Q ?", "expected_facts": ["22 EUR"]}\n'
        '{"id": "u01", "category": "unanswerable", "question": "R ?", "expected_facts": []}\n',
        encoding="utf-8",
    )

    items = load_items(path)

    assert [item.id for item in items] == ["d01", "u01"]
    assert items[0].expected_facts == ("22 EUR",)
    assert items[1].expected_facts == ()


def test_judge_cache_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "cache.jsonl"
    cache = JudgeCache(path)
    key = cache_key("model", "question", "answer")
    verdict = Verdict(refusal=False, supported=True, unsupported_claims=[])

    assert cache.get(key) is None
    cache.put(key, verdict)

    reloaded = JudgeCache(path)
    assert reloaded.get(key) == verdict
    assert cache_key("model", "question", "answer") == key
    assert cache_key("model", "question", "other") != key
