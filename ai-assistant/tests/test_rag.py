from app.rag.knowledge_store import KnowledgeStore


def test_knowledge_store_returns_matching_docs():
    store = KnowledgeStore()
    results = store.search("sleep quality")
    assert len(results) > 0
    assert results[0]["title"]


def test_knowledge_store_status_reports_ok():
    store = KnowledgeStore()
    status = store.status()
    assert status["document_count"] >= 1
    assert status["evidence_available"] is True


def test_official_nasa_sources_are_citable():
    store = KnowledgeStore()
    results = store.search("bone density")
    assert len(results) > 0
    official = [item for item in results if "nasa.gov" in str(item.get("source_url", "")).lower()]
    assert len(official) > 0
    assert all(item.get("title") and item.get("source_url", "").startswith("http") for item in official)
