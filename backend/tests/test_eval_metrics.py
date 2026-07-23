from local_rag.eval_retrieval import LabeledQuestion, first_relevant_rank, mrr, recall_at_k
from local_rag.retrieval import RetrievedChunk


def _chunk(doc: str, section: str) -> RetrievedChunk:
    return RetrievedChunk(doc=doc, section=section, pages=(1,), text="", score=0.5)


def test_first_relevant_rank_matches_doc_and_section():
    expected = LabeledQuestion("q", "manuel_rh", ("Teletravail",))
    results = [
        _chunk("guide_onboarding", "4. Teletravail"),
        _chunk("manuel_rh", "2. Temps de travail"),
        _chunk("manuel_rh", "4. Teletravail"),
    ]
    assert first_relevant_rank(results, expected) == 3


def test_first_relevant_rank_accepts_any_labeled_section():
    expected = LabeledQuestion("q", "guide_onboarding", ("Contacts utiles", "Comptes et outils"))
    results = [_chunk("guide_onboarding", "4. Comptes et outils")]
    assert first_relevant_rank(results, expected) == 1


def test_first_relevant_rank_returns_none_when_absent():
    expected = LabeledQuestion("q", "manuel_rh", ("Formation",))
    results = [_chunk("manuel_rh", "1. Objet")]
    assert first_relevant_rank(results, expected) is None


def test_recall_at_k():
    ranks = [1, 4, None, 2]
    assert recall_at_k(ranks, 1) == 0.25
    assert recall_at_k(ranks, 3) == 0.5
    assert recall_at_k(ranks, 5) == 0.75


def test_mrr():
    ranks = [1, 2, None]
    assert mrr(ranks) == (1 + 0.5) / 3
