import pytest
from unittest.mock import MagicMock, call


def make_text_response(text):
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def make_tool_use_response(tool_name, tool_input, tool_use_id="tu_1"):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_input
    tool_block.id = tool_use_id
    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [tool_block]
    return response


@pytest.fixture
def mock_anthropic(mocker):
    mock_client = MagicMock()
    mocker.patch("ai_generator.anthropic.Anthropic", return_value=mock_client)
    return mock_client


@pytest.fixture
def generator(mock_anthropic):
    from ai_generator import AIGenerator

    return AIGenerator(api_key="test", model="claude-test")


@pytest.fixture
def mock_tool_manager():
    mgr = MagicMock()
    mgr.execute_tool.return_value = "tool result"
    return mgr


# --- Tests ---


def test_direct_response_no_tool_use(generator, mock_anthropic):
    mock_anthropic.messages.create.return_value = make_text_response("Direct answer")
    result = generator.generate_response(query="What is Python?")
    assert result == "Direct answer"
    assert mock_anthropic.messages.create.call_count == 1


def test_tool_use_triggers_second_call(generator, mock_anthropic, mock_tool_manager):
    first = make_tool_use_response("search_course_content", {"query": "python"})
    second = make_text_response("Final answer")
    mock_anthropic.messages.create.side_effect = [first, second]
    tools = [{"name": "search_course_content"}]

    generator.generate_response(
        query="Tell me about Python", tools=tools, tool_manager=mock_tool_manager
    )

    assert mock_anthropic.messages.create.call_count == 2


def test_tool_manager_execute_called_correctly(
    generator, mock_anthropic, mock_tool_manager
):
    first = make_tool_use_response("search_course_content", {"query": "python"})
    second = make_text_response("Final answer")
    mock_anthropic.messages.create.side_effect = [first, second]
    tools = [{"name": "search_course_content"}]

    generator.generate_response(
        query="Tell me about Python", tools=tools, tool_manager=mock_tool_manager
    )

    mock_tool_manager.execute_tool.assert_called_once_with(
        "search_course_content", query="python"
    )


def test_final_synthesis_call_has_no_tools(
    generator, mock_anthropic, mock_tool_manager
):
    # Two tool rounds: synthesis is the 3rd call and must have no tools
    first = make_tool_use_response("get_course_outline", {"course_name": "Python"})
    second = make_tool_use_response("search_course_content", {"query": "topic"})
    third = make_text_response("Final answer")
    mock_anthropic.messages.create.side_effect = [first, second, third]
    tools = [{"name": "get_course_outline"}, {"name": "search_course_content"}]

    generator.generate_response(
        query="Find related course", tools=tools, tool_manager=mock_tool_manager
    )

    last_call_kwargs = mock_anthropic.messages.create.call_args_list[-1].kwargs
    assert "tools" not in last_call_kwargs
    assert "tool_choice" not in last_call_kwargs


def test_second_call_messages_structure(generator, mock_anthropic, mock_tool_manager):
    first = make_tool_use_response(
        "search_course_content", {"query": "python"}, tool_use_id="tu_abc"
    )
    second = make_text_response("Final answer")
    mock_anthropic.messages.create.side_effect = [first, second]
    tools = [{"name": "search_course_content"}]

    generator.generate_response(
        query="Tell me about Python", tools=tools, tool_manager=mock_tool_manager
    )

    second_call_kwargs = mock_anthropic.messages.create.call_args_list[1].kwargs
    messages = second_call_kwargs["messages"]
    # 3 messages: original user, assistant tool use, tool result
    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    tool_result_content = messages[2]["content"]
    assert isinstance(tool_result_content, list)
    assert tool_result_content[0]["type"] == "tool_result"
    assert tool_result_content[0]["tool_use_id"] == "tu_abc"


def test_conversation_history_in_system_prompt(generator, mock_anthropic):
    mock_anthropic.messages.create.return_value = make_text_response("Answer")
    history = "User: hi\nAssistant: hello"
    generator.generate_response(query="Next question", conversation_history=history)

    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert history in call_kwargs["system"]


def test_no_conversation_history(generator, mock_anthropic):
    from ai_generator import AIGenerator

    mock_anthropic.messages.create.return_value = make_text_response("Answer")
    generator.generate_response(query="A question")

    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert call_kwargs["system"] == AIGenerator.SYSTEM_PROMPT


def test_no_tools_no_tool_choice_in_api_call(generator, mock_anthropic):
    mock_anthropic.messages.create.return_value = make_text_response("Answer")
    generator.generate_response(query="A question", tools=None)

    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert "tools" not in call_kwargs
    assert "tool_choice" not in call_kwargs


# --- Two-round tool use tests ---


def test_two_round_tool_use_makes_three_api_calls(
    generator, mock_anthropic, mock_tool_manager
):
    first = make_tool_use_response("get_course_outline", {"course_name": "Python"})
    second = make_tool_use_response("search_course_content", {"query": "topic"})
    third = make_text_response("Final answer")
    mock_anthropic.messages.create.side_effect = [first, second, third]
    tools = [{"name": "get_course_outline"}, {"name": "search_course_content"}]

    result = generator.generate_response(
        query="Find related course", tools=tools, tool_manager=mock_tool_manager
    )

    assert mock_anthropic.messages.create.call_count == 3
    assert result == "Final answer"


def test_two_rounds_tools_executed_twice(generator, mock_anthropic, mock_tool_manager):
    first = make_tool_use_response(
        "get_course_outline", {"course_name": "Python"}, tool_use_id="tu_1"
    )
    second = make_tool_use_response(
        "search_course_content", {"query": "topic"}, tool_use_id="tu_2"
    )
    third = make_text_response("Final answer")
    mock_anthropic.messages.create.side_effect = [first, second, third]
    tools = [{"name": "get_course_outline"}, {"name": "search_course_content"}]

    generator.generate_response(
        query="Find related course", tools=tools, tool_manager=mock_tool_manager
    )

    assert mock_tool_manager.execute_tool.call_count == 2


def test_two_rounds_final_call_has_no_tools(
    generator, mock_anthropic, mock_tool_manager
):
    first = make_tool_use_response("get_course_outline", {"course_name": "Python"})
    second = make_tool_use_response("search_course_content", {"query": "topic"})
    third = make_text_response("Final answer")
    mock_anthropic.messages.create.side_effect = [first, second, third]
    tools = [{"name": "get_course_outline"}, {"name": "search_course_content"}]

    generator.generate_response(
        query="Find related course", tools=tools, tool_manager=mock_tool_manager
    )

    third_call_kwargs = mock_anthropic.messages.create.call_args_list[2].kwargs
    assert "tools" not in third_call_kwargs
    assert "tool_choice" not in third_call_kwargs


def test_two_rounds_message_structure(generator, mock_anthropic, mock_tool_manager):
    first = make_tool_use_response(
        "get_course_outline", {"course_name": "Python"}, tool_use_id="tu_1"
    )
    second = make_tool_use_response(
        "search_course_content", {"query": "topic"}, tool_use_id="tu_2"
    )
    third = make_text_response("Final answer")
    mock_anthropic.messages.create.side_effect = [first, second, third]
    tools = [{"name": "get_course_outline"}, {"name": "search_course_content"}]

    generator.generate_response(
        query="Find related course", tools=tools, tool_manager=mock_tool_manager
    )

    third_call_kwargs = mock_anthropic.messages.create.call_args_list[2].kwargs
    messages = third_call_kwargs["messages"]
    # 5 messages: original user, assistant R1, tool_result R1, assistant R2, tool_result R2
    assert len(messages) == 5
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"
    assert messages[4]["role"] == "user"
    assert messages[2]["content"][0]["tool_use_id"] == "tu_1"
    assert messages[4]["content"][0]["tool_use_id"] == "tu_2"


def test_early_termination_when_intermediate_returns_text(
    generator, mock_anthropic, mock_tool_manager
):
    first = make_tool_use_response("search_course_content", {"query": "python"})
    second = make_text_response("Direct answer after round 1")
    mock_anthropic.messages.create.side_effect = [first, second]
    tools = [{"name": "search_course_content"}]

    result = generator.generate_response(
        query="Tell me about Python", tools=tools, tool_manager=mock_tool_manager
    )

    assert mock_anthropic.messages.create.call_count == 2
    assert result == "Direct answer after round 1"


def test_tool_execution_error_does_not_raise(
    generator, mock_anthropic, mock_tool_manager
):
    first = make_tool_use_response("search_course_content", {"query": "python"})
    second = make_text_response("Answer despite error")
    mock_anthropic.messages.create.side_effect = [first, second]
    mock_tool_manager.execute_tool.side_effect = RuntimeError("DB unavailable")
    tools = [{"name": "search_course_content"}]

    result = generator.generate_response(
        query="Tell me about Python", tools=tools, tool_manager=mock_tool_manager
    )

    assert result == "Answer despite error"
    # Error string should appear in the tool_result sent to the intermediate call
    second_call_kwargs = mock_anthropic.messages.create.call_args_list[1].kwargs
    tool_result_content = second_call_kwargs["messages"][2]["content"]
    assert any(
        "Error executing tool" in item["content"] for item in tool_result_content
    )
