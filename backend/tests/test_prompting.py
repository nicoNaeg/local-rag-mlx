from local_rag.prompting import EMPTY_CONTEXT, SYSTEM_PROMPT, build_messages
from local_rag.retrieval import RetrievedChunk


def chunk(doc: str, section: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(doc=doc, section=section, pages=(3, 4), text=text, score=0.9)


def test_messages_structure() -> None:
    messages = build_messages("Quel est le plafond ?", [chunk("frais", "Plafonds", "22 EUR.")])

    assert [message["role"] for message in messages] == ["system", "user"]
    assert messages[0]["content"] == SYSTEM_PROMPT


def test_excerpts_are_numbered_with_metadata() -> None:
    chunks = [chunk("frais", "Plafonds", "22 EUR."), chunk("rh", "Conges", "25 jours.")]

    user = build_messages("Combien de jours ?", chunks)[1]["content"]

    assert "[1] frais, Plafonds (p. 3, 4)\n22 EUR." in user
    assert "[2] rh, Conges (p. 3, 4)\n25 jours." in user
    assert user.endswith("Question: Combien de jours ?")


def test_empty_context_is_explicit() -> None:
    user = build_messages("Question sans support", [])[1]["content"]

    assert EMPTY_CONTEXT in user
