from utils.vector_store import HybridVectorStore


def test_vector_store_add_search_and_persist(tmp_path):
    vs = HybridVectorStore(dim=3)
    vs.add_documents([[1, 0, 0], [0, 1, 0], [0, 0, 1]], ids=["a", "b", "c"])
    # 查询接近第一个向量
    res = vs.search([1, 0, 0], top_k=2)
    assert len(res) == 2
    assert res[0][0] in {"a", "b", "c"}

    path = tmp_path / "idx.json"
    vs.save(str(path))
    assert path.is_file()

    vs2 = HybridVectorStore.load(str(path))
    assert vs2.size == 3
    res2 = vs2.search([0, 1, 0], top_k=1)
    assert len(res2) == 1
