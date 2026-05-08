from app.services.chunk_text import chunk_text


def test_chunk_preserves_order():
    s = "a" * 500 + "\n\n" + "b" * 500
    chunks = chunk_text(s, max_chars=400, overlap=50)
    assert len(chunks) >= 2
    assert chunks[0].startswith("a")


def test_chunk_empty():
    assert chunk_text("") == []


def test_chunk_single_short():
    assert chunk_text("hello", max_chars=900, overlap=80) == ["hello"]
