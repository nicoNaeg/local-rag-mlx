from local_rag.chunking import Block, chunk_blocks, split_long


def test_heading_sets_section_and_pages():
    blocks = [
        Block("heading", "Conges payes", 1),
        Block("text", "Les salaries disposent de vingt-cinq jours ouvres de conges payes." * 4, 2),
    ]
    chunks = chunk_blocks("manuel_rh", blocks)
    assert len(chunks) == 1
    assert chunks[0].section == "Conges payes"
    assert chunks[0].doc == "manuel_rh"
    assert chunks[0].pages == (2,)


def test_same_level_heading_flushes_previous_section():
    paragraph = "Contenu de section suffisamment long pour ne pas etre fusionne. " * 5
    blocks = [
        Block("heading", "Section A", 1),
        Block("text", paragraph, 1),
        Block("heading", "Section B", 1),
        Block("text", paragraph, 2),
    ]
    chunks = chunk_blocks("doc", blocks)
    assert [chunk.section for chunk in chunks] == ["Section A", "Section B"]


def test_long_text_is_split_with_overlap():
    text = "Une phrase complete qui se termine par un point. " * 120
    pieces = split_long(text.strip(), maximum=2000, overlap=200)
    assert len(pieces) > 1
    assert all(len(piece) <= 2000 for piece in pieces)
    assert pieces[1][:40] in pieces[0]


def test_tiny_trailing_text_merges_into_previous_chunk():
    blocks = [
        Block("heading", "Section", 1),
        Block("text", "Paragraphe principal de la section. " * 45, 1),
        Block("text", "Note breve.", 1),
    ]
    chunks = chunk_blocks("doc", blocks)
    assert len(chunks) == 1
    assert "Note breve." in chunks[0].text


def test_table_is_kept_as_its_own_chunk():
    paragraph = "Texte introductif place avant le tableau des plafonds. " * 5
    blocks = [
        Block("heading", "Plafonds", 1),
        Block("text", paragraph, 1),
        Block("table", "| Type | Plafond |\n| Repas | 22 EUR |", 1),
    ]
    chunks = chunk_blocks("doc", blocks)
    assert len(chunks) == 2
    assert chunks[1].text.startswith("| Type |")
