"""
backend/models.py
State management, in-memory dataset store, and conversation session models.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class DatasetStore:
    """Singleton/In-memory store managing active datasets and caching statistics."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatasetStore, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_path: Optional[str] = None):
        if self._initialized:
            return
        self.df: pd.DataFrame = pd.DataFrame()
        self.active_file_path: Optional[str] = data_path
        self.metadata: Dict[str, Any] = {}
        self.cached_kpis: Optional[Dict[str, Any]] = None
        self._initialized = True

    def set_data(self, df: pd.DataFrame, file_path: Optional[str] = None):
        """Sets the active dataframe and invalidates cache."""
        self.df = df
        self.active_file_path = file_path
        self.cached_kpis = None
        self._update_metadata()

    def get_data(self) -> pd.DataFrame:
        """Returns the current dataframe."""
        return self.df

    def _update_metadata(self):
        """Precomputes summary metadata."""
        if self.df.empty:
            self.metadata = {
                "total_records": 0,
                "columns": [],
                "date_range": None
            }
            return

        date_col = 'date' if 'date' in self.df.columns else None
        min_date, max_date = None, None
        if date_col and pd.api.types.is_datetime64_any_dtype(self.df[date_col]):
            valid_dates = self.df[date_col].dropna()
            if not valid_dates.empty:
                min_date = str(valid_dates.min().strftime('%Y-%m-%d'))
                max_date = str(valid_dates.max().strftime('%Y-%m-%d'))

        self.metadata = {
            "total_records": len(self.df),
            "columns": list(self.df.columns),
            "date_range": {"min": min_date, "max": max_date} if min_date else None,
            "categories": list(self.df['category'].dropna().unique()[:15]) if 'category' in self.df.columns else [],
            "statuses": list(self.df['status'].dropna().unique()[:10]) if 'status' in self.df.columns else []
        }


class ChatMessage:
    """Represents an interaction between user and the autonomous analyst."""
    def __init__(
        self,
        sender: str,
        text: str,
        intent: Optional[str] = None,
        chart_url: Optional[str] = None,
        data_table: Optional[List[Dict[str, Any]]] = None,
        suggestions: Optional[List[str]] = None
    ):
        self.id = f"msg_{int(time.time() * 1000)}"
        self.sender = sender  # 'user' or 'analyst'
        self.text = text
        self.intent = intent
        self.chart_url = chart_url
        self.data_table = data_table or []
        self.suggestions = suggestions or []
        self.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "text": self.text,
            "intent": self.intent,
            "chart_url": self.chart_url,
            "data_table": self.data_table,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp
        }


class ConversationManager:
    """Manages chat history per session."""
    def __init__(self):
        self.sessions: Dict[str, List[ChatMessage]] = {}

    def add_message(self, session_id: str, message: ChatMessage):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(message)

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        messages = self.sessions.get(session_id, [])
        return [m.to_dict() for m in messages]

    def clear(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id] = []


# Global Singletons
dataset_store = DatasetStore()
conversation_manager = ConversationManager()
