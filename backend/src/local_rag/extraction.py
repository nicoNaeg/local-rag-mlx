from functools import lru_cache
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc import DocItemLabel, TableItem

from local_rag.chunking import Block

_HEADING_LABELS = {DocItemLabel.SECTION_HEADER}
_SKIP_LABELS = {
    DocItemLabel.PAGE_HEADER,
    DocItemLabel.PAGE_FOOTER,
    DocItemLabel.FOOTNOTE,
    DocItemLabel.TITLE,
}


@lru_cache(maxsize=1)
def _converter() -> DocumentConverter:
    return DocumentConverter()


def extract_blocks(path: Path) -> list[Block]:
    document = _converter().convert(path).document
    blocks: list[Block] = []
    page = 1
    for item, _ in document.iterate_items():
        prov = getattr(item, "prov", None)
        if prov:
            page = prov[0].page_no
        if isinstance(item, TableItem):
            markdown = item.export_to_markdown(doc=document).strip()
            if markdown:
                blocks.append(Block("table", markdown, page))
            continue
        label = getattr(item, "label", None)
        if label in _SKIP_LABELS:
            continue
        text = (getattr(item, "text", "") or "").strip()
        if not text:
            continue
        if label in _HEADING_LABELS:
            blocks.append(Block("heading", text, page, level=getattr(item, "level", 1)))
        else:
            blocks.append(Block("text", text, page))
    return blocks
