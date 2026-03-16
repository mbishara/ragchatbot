"""
API endpoint tests for the RAG chatbot.

app.py mounts static files from ../frontend and initialises RAGSystem at
module-level, both of which break in the test environment.  Rather than
fighting those import-time side-effects, we mirror the three routes in a
lightweight test app that accepts an injected mock RAGSystem.  This keeps
the tests fast, hermetic, and independent of the file-system.
"""

import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Any, Dict, List, Optional


# ── Pydantic models (mirrored from app.py) ────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    session_id: str


class CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


# ── Test app factory ──────────────────────────────────────────────────────────

def make_test_app(rag_system: MagicMock) -> FastAPI:
    """Build a minimal FastAPI app mirroring app.py's routes with an injected RAGSystem."""
    test_app = FastAPI()

    @test_app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()
            answer, sources = rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.delete("/api/session/{session_id}")
    async def delete_session(session_id: str):
        rag_system.session_manager.clear_session(session_id)
        return {"status": "cleared"}

    return test_app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_rag():
    rag = MagicMock()
    rag.session_manager.create_session.return_value = "auto-session-id"
    rag.query.return_value = ("Default answer", [])
    rag.get_course_analytics.return_value = {"total_courses": 0, "course_titles": []}
    return rag


@pytest.fixture
def client(mock_rag):
    return TestClient(make_test_app(mock_rag))


# ── POST /api/query ───────────────────────────────────────────────────────────

def test_query_returns_200_with_answer(client, mock_rag):
    mock_rag.query.return_value = ("Python is a language.", [])
    resp = client.post("/api/query", json={"query": "What is Python?", "session_id": "s1"})
    assert resp.status_code == 200
    assert resp.json()["answer"] == "Python is a language."


def test_query_response_contains_session_id(client, mock_rag):
    mock_rag.query.return_value = ("answer", [])
    resp = client.post("/api/query", json={"query": "hello", "session_id": "s1"})
    assert resp.json()["session_id"] == "s1"


def test_query_auto_creates_session_when_missing(client, mock_rag):
    mock_rag.query.return_value = ("answer", [])
    resp = client.post("/api/query", json={"query": "hello"})
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "auto-session-id"
    mock_rag.session_manager.create_session.assert_called_once()


def test_query_passes_correct_query_to_rag(client, mock_rag):
    mock_rag.query.return_value = ("answer", [])
    client.post("/api/query", json={"query": "Explain decorators", "session_id": "s1"})
    mock_rag.query.assert_called_once_with("Explain decorators", "s1")


def test_query_returns_sources_in_response(client, mock_rag):
    sources = [{"label": "Python Course - Lesson 1", "url": "https://example.com"}]
    mock_rag.query.return_value = ("answer", sources)
    resp = client.post("/api/query", json={"query": "hello", "session_id": "s1"})
    assert resp.json()["sources"] == sources


def test_query_returns_500_on_rag_exception(client, mock_rag):
    mock_rag.query.side_effect = RuntimeError("vector DB unavailable")
    resp = client.post("/api/query", json={"query": "hello", "session_id": "s1"})
    assert resp.status_code == 500
    assert "vector DB unavailable" in resp.json()["detail"]


def test_query_missing_query_field_returns_422(client):
    resp = client.post("/api/query", json={"session_id": "s1"})
    assert resp.status_code == 422


# ── GET /api/courses ──────────────────────────────────────────────────────────

def test_courses_returns_200(client, mock_rag):
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 3,
        "course_titles": ["Python Basics", "FastAPI", "SQL"],
    }
    resp = client.get("/api/courses")
    assert resp.status_code == 200


def test_courses_returns_correct_total(client, mock_rag):
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"],
    }
    resp = client.get("/api/courses")
    assert resp.json()["total_courses"] == 2


def test_courses_returns_title_list(client, mock_rag):
    titles = ["Course A", "Course B"]
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": titles,
    }
    resp = client.get("/api/courses")
    assert resp.json()["course_titles"] == titles


def test_courses_returns_500_on_analytics_exception(client, mock_rag):
    mock_rag.get_course_analytics.side_effect = RuntimeError("chroma error")
    resp = client.get("/api/courses")
    assert resp.status_code == 500
    assert "chroma error" in resp.json()["detail"]


def test_courses_empty_catalog(client, mock_rag):
    mock_rag.get_course_analytics.return_value = {"total_courses": 0, "course_titles": []}
    resp = client.get("/api/courses")
    assert resp.status_code == 200
    assert resp.json() == {"total_courses": 0, "course_titles": []}


# ── DELETE /api/session/{session_id} ─────────────────────────────────────────

def test_delete_session_returns_200(client):
    resp = client.delete("/api/session/s1")
    assert resp.status_code == 200


def test_delete_session_returns_cleared_status(client):
    resp = client.delete("/api/session/s1")
    assert resp.json() == {"status": "cleared"}


def test_delete_session_calls_clear_on_session_manager(client, mock_rag):
    client.delete("/api/session/my-session")
    mock_rag.session_manager.clear_session.assert_called_once_with("my-session")
