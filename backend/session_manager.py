import time
from collections import OrderedDict
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a single message in a conversation"""

    role: str  # "user" or "assistant"
    content: str  # The message content


class SessionManager:
    """Manages conversation sessions and message history"""

    def __init__(self, max_history: int = 5, max_sessions: int = 1000, session_ttl_seconds: int = 3600):
        self.max_history = max_history
        self.max_sessions = max_sessions
        self.session_ttl_seconds = session_ttl_seconds
        self.sessions: OrderedDict[str, List[Message]] = OrderedDict()
        self._last_access: Dict[str, float] = {}
        self.session_counter = 0

    def _evict(self):
        """Prune expired sessions, then evict oldest if over max_sessions."""
        now = time.time()
        expired = [
            sid for sid, ts in self._last_access.items()
            if now - ts > self.session_ttl_seconds
        ]
        for sid in expired:
            self.sessions.pop(sid, None)
            self._last_access.pop(sid, None)

        while len(self.sessions) >= self.max_sessions:
            oldest_sid, _ = self.sessions.popitem(last=False)
            self._last_access.pop(oldest_sid, None)

    def create_session(self) -> str:
        """Create a new conversation session"""
        self._evict()
        self.session_counter += 1
        session_id = f"session_{self.session_counter}"
        self.sessions[session_id] = []
        self._last_access[session_id] = time.time()
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the conversation history"""
        self._evict()
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self._last_access[session_id] = time.time()
        # Move to end to reflect recent access
        self.sessions.move_to_end(session_id)

        message = Message(role=role, content=content)
        self.sessions[session_id].append(message)

        # Keep conversation history within limits
        if len(self.sessions[session_id]) > self.max_history * 2:
            self.sessions[session_id] = self.sessions[session_id][
                -self.max_history * 2 :
            ]

    def add_exchange(self, session_id: str, user_message: str, assistant_message: str):
        """Add a complete question-answer exchange"""
        self.add_message(session_id, "user", user_message)
        self.add_message(session_id, "assistant", assistant_message)

    def get_conversation_history(self, session_id: Optional[str]) -> Optional[str]:
        """Get formatted conversation history for a session"""
        self._evict()
        if not session_id or session_id not in self.sessions:
            return None

        self._last_access[session_id] = time.time()
        self.sessions.move_to_end(session_id)

        messages = self.sessions[session_id]
        if not messages:
            return None

        # Format messages for context
        formatted_messages = []
        for msg in messages:
            formatted_messages.append(f"{msg.role.title()}: {msg.content}")

        return "\n".join(formatted_messages)

    def clear_session(self, session_id: str):
        """Clear all messages from a session"""
        if session_id in self.sessions:
            self.sessions[session_id] = []
