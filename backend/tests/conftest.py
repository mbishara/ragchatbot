import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock
from vector_store import SearchResults


# ── Shared vector-store / search fixtures ────────────────────────────────────

@pytest.fixture
def mock_vector_store():
    """A MagicMock standing in for VectorStore with sensible defaults."""
    store = MagicMock()
    store.get_lesson_link.return_value = "https://example.com/lesson"
    store.search.return_value = SearchResults(documents=[], metadata=[], distances=[])
    store.get_course_count.return_value = 0
    store.get_existing_course_titles.return_value = []
    return store


@pytest.fixture
def sample_search_results():
    """A non-empty SearchResults with one document."""
    return SearchResults(
        documents=["Introduction to Python variables and data types."],
        metadata=[{"course_title": "Python Basics", "lesson_number": 1}],
        distances=[0.1],
    )


# ── Shared RAGSystem mock ─────────────────────────────────────────────────────

@pytest.fixture
def mock_rag_system():
    """Fully mocked RAGSystem with safe defaults for API-level tests."""
    rag = MagicMock()
    rag.session_manager.create_session.return_value = "test-session-id"
    rag.query.return_value = ("Default answer", [])
    rag.get_course_analytics.return_value = {"total_courses": 0, "course_titles": []}
    return rag
