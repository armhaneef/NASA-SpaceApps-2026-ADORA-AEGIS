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
    assert all(item.get("title") and item.get("source_url", "").startswith("https://") for item in official)
    assert all(item.get("content_verified") is True for item in official)
    assert all("example.invalid" not in item.get("source_url", "") for item in results)


def test_placeholder_domains_are_not_valid_citations():
    assert KnowledgeStore._is_valid_citation({
        "title": "Placeholder source",
        "source_url": "https://example.invalid/not-a-source",
    }) is False


def test_illustrative_local_knowledge_remains_searchable_without_fake_citation():
    store = KnowledgeStore()

    results = store.search("digital twin monitoring")

    local_note = next(item for item in results if item["document_id"] == "simulated-knowledge-2")
    assert local_note["citation_valid"] is False
    assert local_note["citation_status"] == "illustrative_only"
    assert local_note["source_url"] == ""

    assert KnowledgeStore._is_valid_citation({
        "title": "Malformed source",
        "source_url": "https://[invalid",
    }) is False
