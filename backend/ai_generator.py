import anthropic
from typing import List, Optional, Dict, Any


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Tool Usage:
- Use **`get_course_outline`** for questions about a course's structure, syllabus, lessons, or outline. Return the course title, course link, and every lesson with its number and title.
- Use **`search_course_content`** for questions about specific course content. You may make up to **2 sequential tool calls** if needed (e.g., get an outline then search for related content). Stop tool use as soon as you have enough information.
- Synthesize tool results into accurate, fact-based responses.
- If a tool yields no results, state this clearly without offering alternatives.

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using a tool.
- **Outline / structure questions**: Use `get_course_outline`, then present the full course title, link, and numbered lesson list.
- **Course-specific content questions**: Use `search_course_content`, then answer.
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis.
 - Do not mention "based on the search results".


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
    ) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content,
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get response from Claude
        response = self.client.messages.create(**api_params)

        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)

        # Return direct response
        if not response.content:
            raise ValueError("Claude API returned empty content — possible safety filter or API error")
        return response.content[0].text

    def _execute_tools(self, response, tool_manager) -> list:
        """Execute all tool_use blocks in a response, returning tool_result dicts."""
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                try:
                    result = tool_manager.execute_tool(block.name, **block.input)
                except Exception as e:
                    result = f"Error executing tool '{block.name}': {e}"
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
        return tool_results

    def _handle_tool_execution(
        self, initial_response, base_params: Dict[str, Any], tool_manager
    ):
        """
        Handle up to 2 sequential rounds of tool use before synthesizing a final response.

        Args:
            initial_response: The first tool_use response from generate_response
            base_params: Full API parameters from the first call (includes tools, system, messages)
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution
        """
        messages = base_params["messages"].copy()
        current_response = initial_response  # stop_reason guaranteed "tool_use"

        for tool_round in range(2):
            messages.append({"role": "assistant", "content": current_response.content})
            tool_results = self._execute_tools(current_response, tool_manager)
            messages.append({"role": "user", "content": tool_results})

            if tool_round < 1:  # Round 0: make intermediate call WITH tools
                next_response = self.client.messages.create(
                    **{**base_params, "messages": messages}
                )
                if next_response.stop_reason != "tool_use":
                    if not next_response.content:
                        raise ValueError("Claude API returned empty content — possible safety filter or API error")
                    return next_response.content[0].text  # Claude answered directly
                current_response = next_response
            # Round 1: fall through to final synthesis

        # Final call WITHOUT tools — strip tools by building from base_params
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"],
        }
        final_response = self.client.messages.create(**final_params)
        if not final_response.content:
            raise ValueError("Claude API returned empty content — possible safety filter or API error")
        return final_response.content[0].text
