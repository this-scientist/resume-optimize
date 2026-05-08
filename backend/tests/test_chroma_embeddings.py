from types import SimpleNamespace

from app.services import chroma_store
from app.services.embeddings import embed_chunks


def test_embed_chunks_mock_openai(monkeypatch):
    class FakeEmbeddings:
        def create(self, model, input):
            class Item:
                def __init__(self, i):
                    self.embedding = [float(i), 0.25, 0.5]

            return SimpleNamespace(data=[Item(i) for i in range(len(input))])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.embeddings = FakeEmbeddings()

    monkeypatch.setattr("app.services.embeddings.OpenAI", FakeOpenAI)

    vectors = embed_chunks(["hello", "world"], api_key="sk-test", base_url=None, model="text-embedding-3-small")
    assert len(vectors) == 2
    assert len(vectors[0]) == 3


def test_chroma_add_then_delete_by_source_id(monkeypatch, tmp_path):
    class FakeEmbeddings:
        def create(self, model, input):
            class Item:
                def __init__(self, i):
                    self.embedding = [float(i), 0.0, 1.0]

            return SimpleNamespace(data=[Item(i) for i in range(len(input))])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.embeddings = FakeEmbeddings()

    monkeypatch.setattr("app.services.embeddings.OpenAI", FakeOpenAI)

    data_dir = tmp_path
    texts = ["chunk-a", "chunk-b"]
    vectors = embed_chunks(texts, api_key="k", base_url=None, model="m")

    chroma_store.add_interview_chunks(
        data_dir,
        texts=texts,
        embeddings=vectors,
        source_type="interview_note",
        source_id=42,
    )

    coll = chroma_store.get_collection(data_dir)
    assert coll.count() == 2

    chroma_store.delete_by_source_id(data_dir, 42)
    assert coll.count() == 0
