from app.services.token_budget import clip_chunks


def test_clip_respects_budget_and_order():
    chunks = ["a" * 1000, "b" * 1000]
    out = clip_chunks(chunks, max_chars=1500)
    assert len(out) == 1500
    assert out == "a" * 1000 + "b" * 500


def test_clip_empty():
    assert clip_chunks([], 4000) == ""
    assert clip_chunks(["x"], 0) == ""


def test_clip_truncates_middle_chunk():
    out = clip_chunks(["hello", "worldwide"], max_chars=8)
    assert out == "hellowor"
