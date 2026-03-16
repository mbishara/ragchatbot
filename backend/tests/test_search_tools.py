import pytest
from unittest.mock import MagicMock
from vector_store import SearchResults
from search_tools import CourseSearchTool, ToolManager


def make_results(documents, metadatas, lesson_url="https://example.com/lesson"):
    mock_store = MagicMock()
    mock_store.get_lesson_link.return_value = lesson_url
    results = SearchResults(
        documents=documents,
        metadata=metadatas,
        distances=[0.1] * len(documents),
    )
    return mock_store, results


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.get_lesson_link.return_value = "https://example.com/lesson"
    return store


@pytest.fixture
def tool(mock_store):
    return CourseSearchTool(mock_store)


@pytest.fixture
def manager(mock_store, tool):
    mgr = ToolManager()
    mgr.register_tool(tool)
    return mgr


# --- CourseSearchTool.execute() tests ---

def test_execute_returns_formatted_results(tool, mock_store):
    mock_store.search.return_value = SearchResults(
        documents=["Content about Python"],
        metadata=[{"course_title": "Python Course", "lesson_number": 1}],
        distances=[0.1],
    )
    result = tool.execute(query="python basics")
    assert "[Python Course - Lesson 1]" in result
    assert "Content about Python" in result


def test_execute_no_lesson_number_in_header(tool, mock_store):
    mock_store.search.return_value = SearchResults(
        documents=["Intro content"],
        metadata=[{"course_title": "Python Course"}],
        distances=[0.1],
    )
    result = tool.execute(query="intro")
    assert "[Python Course]" in result
    assert "Lesson" not in result


def test_execute_empty_results_no_filter(tool, mock_store):
    mock_store.search.return_value = SearchResults(documents=[], metadata=[], distances=[])
    result = tool.execute(query="something")
    assert result == "No relevant content found."


def test_execute_empty_results_with_course_filter(tool, mock_store):
    mock_store.search.return_value = SearchResults(documents=[], metadata=[], distances=[])
    result = tool.execute(query="something", course_name="Python")
    assert result == "No relevant content found in course 'Python'."


def test_execute_empty_results_with_lesson_filter(tool, mock_store):
    mock_store.search.return_value = SearchResults(documents=[], metadata=[], distances=[])
    result = tool.execute(query="something", lesson_number=3)
    assert result == "No relevant content found in lesson 3."


def test_execute_empty_results_with_both_filters(tool, mock_store):
    mock_store.search.return_value = SearchResults(documents=[], metadata=[], distances=[])
    result = tool.execute(query="something", course_name="Python", lesson_number=3)
    assert result == "No relevant content found in course 'Python' in lesson 3."


def test_execute_error_propagated(tool, mock_store):
    mock_store.search.return_value = SearchResults(
        documents=[], metadata=[], distances=[], error="DB error"
    )
    result = tool.execute(query="something")
    assert result == "DB error"


def test_execute_populates_last_sources(tool, mock_store):
    mock_store.search.return_value = SearchResults(
        documents=["Content"],
        metadata=[{"course_title": "Python Course", "lesson_number": 1}],
        distances=[0.1],
    )
    mock_store.get_lesson_link.return_value = "https://example.com/lesson1"
    tool.execute(query="python")
    assert tool.last_sources == [{"label": "Python Course - Lesson 1", "url": "https://example.com/lesson1"}]


def test_execute_deduplicates_sources(tool, mock_store):
    mock_store.search.return_value = SearchResults(
        documents=["Doc A", "Doc B"],
        metadata=[
            {"course_title": "Python Course", "lesson_number": 1},
            {"course_title": "Python Course", "lesson_number": 1},
        ],
        distances=[0.1, 0.2],
    )
    tool.execute(query="python")
    assert len(tool.last_sources) == 1


def test_execute_multiple_results_joined(tool, mock_store):
    mock_store.search.return_value = SearchResults(
        documents=["Doc A", "Doc B"],
        metadata=[
            {"course_title": "Python Course", "lesson_number": 1},
            {"course_title": "Python Course", "lesson_number": 2},
        ],
        distances=[0.1, 0.2],
    )
    result = tool.execute(query="python")
    assert "\n\n" in result


# --- ToolManager tests ---

def test_tool_manager_get_last_sources(manager, tool, mock_store):
    mock_store.search.return_value = SearchResults(
        documents=["Content"],
        metadata=[{"course_title": "Python Course", "lesson_number": 1}],
        distances=[0.1],
    )
    manager.execute_tool("search_course_content", query="python")
    sources = manager.get_last_sources()
    assert sources == tool.last_sources


def test_tool_manager_reset_sources(manager, tool, mock_store):
    mock_store.search.return_value = SearchResults(
        documents=["Content"],
        metadata=[{"course_title": "Python Course", "lesson_number": 1}],
        distances=[0.1],
    )
    manager.execute_tool("search_course_content", query="python")
    manager.reset_sources()
    assert tool.last_sources == []
