import pytest

faiss = pytest.importorskip("faiss", reason="faiss not installed")

from utils.faiss_store import FaissVectorStore  # noqa: E402


def test_faiss_store_add_search_and_persist(tmp_path):
    vs = FaissVectorStore(dim=3)
    vs.add_documents([[1, 0, 0], [0, 1, 0], [0, 0, 1]], ids=["a", "b", "c"])
    res = vs.search([1, 0, 0], top_k=2)
    assert len(res) == 2
    assert res[0][0] in {"a", "b", "c"}

    p = tmp_path / "faiss_idx.json"
    vs.save(str(p))
    assert p.is_file()

    vs2 = FaissVectorStore.load(str(p))
    assert vs2.size == 3
    res2 = vs2.search([0, 1, 0], top_k=1)
    assert len(res2) == 1
