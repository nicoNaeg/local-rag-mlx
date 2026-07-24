from local_rag.generation import Message
from local_rag.retrieval import RetrievedChunk

SYSTEM_PROMPT = (
    "You are the documentation assistant of Solencia, a renewable-energy company. "
    "Answer strictly from the numbered excerpts provided with the question. "
    "After each claim, cite the excerpt supporting it with its bracketed number, like [2]. "
    "If the excerpts do not contain the answer, say so plainly instead of guessing. "
    "Answer in the language of the question. Be concise."
)

EMPTY_CONTEXT = "No excerpt matched the question."


def format_excerpts(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for number, chunk in enumerate(chunks, start=1):
        pages = ", ".join(str(page) for page in chunk.pages)
        blocks.append(f"[{number}] {chunk.doc}, {chunk.section} (p. {pages})\n{chunk.text}")
    return "\n\n".join(blocks) if blocks else EMPTY_CONTEXT


def build_messages(question: str, chunks: list[RetrievedChunk]) -> list[Message]:
    user = f"Excerpts:\n\n{format_excerpts(chunks)}\n\nQuestion: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
