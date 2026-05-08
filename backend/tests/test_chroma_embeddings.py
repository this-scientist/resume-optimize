import numpy as np

from app.services import chroma_store
from app.services.embeddings import embed_corpus


def test_embed_corpus_mock_flag_model(monkeypatch):
    class FakeModel:
        def __init__(self, *a, **k):
            pass

        def encode_corpus(self, texts, batch_size=None, **kwargs):
            return np.array([[float(i), 0.25, 0.5] for i in range(len(texts))], dtype=np.float32)

    monkeypatch.setattr("app.services.embeddings.FlagModel", FakeModel)

    vectors = embed_corpus(["hello", "world"], model="BAAI/bge-small-zh-v1.5")
    assert len(vectors) == 2
    assert len(vectors[0]) == 3


def test_chroma_add_then_delete_by_source_id(monkeypatch, tmp_path):
    class FakeModel:
        def __init__(self, *a, **k):
            pass

        def encode_corpus(self, texts, batch_size=None, **kwargs):
            return np.array([[float(i), 0.0, 1.0] for i in range(len(texts))], dtype=np.float32)

    monkeypatch.setattr("app.services.embeddings.FlagModel", FakeModel)

    data_dir = tmp_path
    texts = ["chunk-a", "chunk-b"]
    vectors = embed_corpus(texts, model="m")

    chroma_store.add_interview_chunks(
        data_dir,
        texts=texts,
        embeddings=vectors,
        source_type="interview_note",
        source_id=42,
        model_name="m",
    )

    coll = chroma_store.get_collection(data_dir, "m")
    assert coll.count() == 2

    chroma_store.delete_by_source_id(data_dir, 42, "m")
    assert coll.count() == 0
