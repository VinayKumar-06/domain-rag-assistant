from app.ingestion.documents import DocumentError, PageText, chunk_pages, document_id, parse_document


def test_text_parsing_and_content_addressed_id():
    raw = b"A heading\n\nA useful paragraph."
    pages = parse_document("notes.md", raw)
    assert pages[0].text == "A heading\n\nA useful paragraph."
    assert document_id("notes.md", raw) == document_id("notes.md", raw)
    assert document_id("notes.md", raw) != document_id("notes.md", b"other")


def test_empty_and_unsupported_files_are_rejected():
    for filename, content in [("empty.txt", b""), ("payload.exe", b"x")]:
        try:
            parse_document(filename, content)
        except DocumentError:
            pass
        else:
            raise AssertionError("expected DocumentError")


def test_chunks_overlap_and_keep_page_metadata():
    chunks = chunk_pages([PageText(3, "abcdefghij klmnopqrst")], filename="paper.txt",
                         doc_id="id", chunk_size=10, overlap=2)
    assert len(chunks) > 1
    assert all(chunk.page == 3 and chunk.filename == "paper.txt" for chunk in chunks)
