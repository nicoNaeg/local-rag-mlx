from dataclasses import dataclass


@dataclass(frozen=True)
class Block:
    kind: str
    text: str
    page: int
    level: int = 1


@dataclass
class Chunk:
    doc: str
    section: str
    text: str
    pages: tuple[int, ...]


def split_long(text: str, maximum: int, overlap: int) -> list[str]:
    pieces: list[str] = []
    start = 0
    while True:
        end = min(start + maximum, len(text))
        if end < len(text):
            cut = text.rfind(". ", start, end)
            if cut > start + maximum // 2:
                end = cut + 1
        pieces.append(text[start:end].strip())
        if end >= len(text):
            return pieces
        start = end - overlap if end - overlap > start else end


def chunk_blocks(
    doc: str,
    blocks: list[Block],
    target: int = 1400,
    maximum: int = 2000,
    overlap: int = 200,
    minimum: int = 200,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    stack: list[tuple[int, str]] = []
    buffer: list[tuple[str, int]] = []

    def section() -> str:
        return " > ".join(title for _, title in stack)

    atomic_ids: set[int] = set()

    def emit(text: str, pages: tuple[int, ...], atomic: bool = False) -> None:
        mergeable = (
            not atomic
            and len(text) < minimum
            and chunks
            and chunks[-1].section == section()
            and id(chunks[-1]) not in atomic_ids
        )
        if mergeable:
            previous = chunks[-1]
            previous.text = previous.text + "\n\n" + text
            previous.pages = tuple(sorted(set(previous.pages) | set(pages)))
            return
        chunk = Chunk(doc, section(), text, pages)
        chunks.append(chunk)
        if atomic:
            atomic_ids.add(id(chunk))

    def flush() -> None:
        if not buffer:
            return
        text = "\n\n".join(part for part, _ in buffer)
        pages = tuple(sorted({page for _, page in buffer}))
        buffer.clear()
        emit(text, pages)

    for block in blocks:
        if block.kind == "heading":
            flush()
            while stack and stack[-1][0] >= block.level:
                stack.pop()
            stack.append((block.level, block.text))
        elif block.kind == "table":
            flush()
            emit(block.text, (block.page,), atomic=True)
        elif len(block.text) > maximum:
            flush()
            for piece in split_long(block.text, maximum, overlap):
                emit(piece, (block.page,))
        else:
            if sum(len(part) for part, _ in buffer) + len(block.text) > maximum:
                flush()
            buffer.append((block.text, block.page))
            if sum(len(part) for part, _ in buffer) >= target:
                flush()
    flush()
    return chunks
