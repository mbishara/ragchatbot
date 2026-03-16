import pytest
from unittest.mock import MagicMock, call


@pytest.fixture
def rag(mocker):
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.AIGenerator")
    mocker.patch("rag_system.DocumentProcessor")
    mocker.patch("rag_system.SessionManager")
    from rag_system import RAGSystem
    cfg = MagicMock()
    system = RAGSystem(cfg)
    # Replace with controllable mocks
    system.ai_generator = MagicMock()
    system.tool_manager = MagicMock()
    system.session_manager = MagicMock()
    return system


def test_query_returns_response_and_sources(rag):
    rag.ai_generator.generate_response.return_value = "Here is the answer"
    sources = [{"label": "Python Course - Lesson 1", "url": "https://example.com"}]
    rag.tool_manager.get_last_sources.return_value = sources

    response, returned_sources = rag.query("What is Python?")

    assert response == "Here is the answer"
    assert returned_sources == sources


def test_query_prompt_formatted_correctly(rag):
    rag.ai_generator.generate_response.return_value = "answer"
    rag.tool_manager.get_last_sources.return_value = []

    rag.query("What is Python?")

    call_kwargs = rag.ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["query"].startswith("Answer this question about course materials:")


def test_query_passes_tools_to_generator(rag):
    rag.ai_generator.generate_response.return_value = "answer"
    rag.tool_manager.get_last_sources.return_value = []
    tool_defs = [{"name": "search_course_content"}]
    rag.tool_manager.get_tool_definitions.return_value = tool_defs

    rag.query("What is Python?")

    call_kwargs = rag.ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["tools"] == tool_defs


def test_query_sources_reset_after_retrieval(rag):
    rag.ai_generator.generate_response.return_value = "answer"
    rag.tool_manager.get_last_sources.return_value = []

    rag.query("What is Python?")

    rag.tool_manager.reset_sources.assert_called_once()
    # Ensure reset is called after get_last_sources
    get_idx = None
    reset_idx = None
    for i, c in enumerate(rag.tool_manager.method_calls):
        if c[0] == "get_last_sources":
            get_idx = i
        if c[0] == "reset_sources":
            reset_idx = i
    assert get_idx is not None and reset_idx is not None
    assert reset_idx > get_idx


def test_query_with_session_fetches_history(rag):
    rag.ai_generator.generate_response.return_value = "answer"
    rag.tool_manager.get_last_sources.return_value = []
    rag.session_manager.get_conversation_history.return_value = "User: hi\nAssistant: hello"

    rag.query("What is Python?", session_id="s1")

    rag.session_manager.get_conversation_history.assert_called_once_with("s1")


def test_query_with_session_updates_history(rag):
    rag.ai_generator.generate_response.return_value = "Final answer"
    rag.tool_manager.get_last_sources.return_value = []

    rag.query("What is Python?", session_id="s1")

    rag.session_manager.add_exchange.assert_called_once_with("s1", "What is Python?", "Final answer")


def test_query_no_session_no_history_call(rag):
    rag.ai_generator.generate_response.return_value = "answer"
    rag.tool_manager.get_last_sources.return_value = []

    rag.query("What is Python?", session_id=None)

    rag.session_manager.get_conversation_history.assert_not_called()


def test_query_two_tools_registered_at_init(mocker):
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.AIGenerator")
    mocker.patch("rag_system.DocumentProcessor")
    mocker.patch("rag_system.SessionManager")
    from rag_system import RAGSystem
    cfg = MagicMock()
    system = RAGSystem(cfg)
    assert len(system.tool_manager.tools) == 2
