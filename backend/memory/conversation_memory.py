import logging
from typing import List, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConversationMemory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = defaultdict(list)
            cls._instance._video_context = {}
        return cls._instance

    def add_message(self, session_id: str, role: str, content: str):
        self._sessions[session_id].append({
            "role": role,
            "content": content,
        })

        max_messages = 50
        if len(self._sessions[session_id]) > max_messages:
            self._sessions[session_id] = self._sessions[session_id][-max_messages:]

    def get_history(self, session_id: str, last_n: int = 10) -> List[Dict[str, str]]:
        history = self._sessions.get(session_id, [])
        return history[-last_n:] if last_n else history

    def get_formatted_history(self, session_id: str, last_n: int = 6) -> str:
        history = self.get_history(session_id, last_n)
        if not history:
            return ""
        formatted = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)

    def set_video_context(self, session_id: str, video_a_meta: dict, video_b_meta: dict):
        self._video_context[session_id] = {
            "video_a": video_a_meta,
            "video_b": video_b_meta,
        }

    def get_video_context(self, session_id: str) -> dict:
        return self._video_context.get(session_id, {})

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._video_context:
            del self._video_context[session_id]

    def clear_all(self):
        self._sessions.clear()
        self._video_context.clear()