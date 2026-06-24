"""
Session storage implementations for conversation state persistence.

Provides both in-memory and SQLite-based session storage for maintaining
conversation context across multiple interactions.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import threading

from src.schemas.message import ConversationContext


class SessionStore(ABC):
    """Abstract base class for session storage."""
    
    @abstractmethod
    def get(self, session_id: str) -> Optional[ConversationContext]:
        """Retrieve a session by ID."""
        pass
    
    @abstractmethod
    def save(self, context: ConversationContext) -> None:
        """Save or update a session."""
        pass
    
    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        pass
    
    @abstractmethod
    def cleanup_expired(self, max_age_minutes: int = 30) -> int:
        """Remove expired sessions. Returns count of removed sessions."""
        pass


class InMemorySessionStore(SessionStore):
    """Simple in-memory session storage (non-persistent)."""
    
    def __init__(self):
        self._sessions: dict[str, ConversationContext] = {}
        self._lock = threading.Lock()
    
    def get(self, session_id: str) -> Optional[ConversationContext]:
        with self._lock:
            return self._sessions.get(session_id)
    
    def save(self, context: ConversationContext) -> None:
        with self._lock:
            context.last_activity = datetime.utcnow()
            self._sessions[context.session_id] = context
    
    def delete(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def cleanup_expired(self, max_age_minutes: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        removed = 0
        with self._lock:
            expired = [
                sid for sid, ctx in self._sessions.items()
                if ctx.last_activity < cutoff
            ]
            for sid in expired:
                del self._sessions[sid]
                removed += 1
        return removed


class SQLiteSessionStore(SessionStore):
    """
    SQLite-based session storage for persistence across restarts.
    
    Stores conversation context in a local SQLite database, enabling:
    - Session persistence across application restarts
    - Multi-turn conversation continuity
    - Automatic cleanup of expired sessions
    """
    
    def __init__(self, db_path: str = "data/sessions.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
    
    @property
    def _conn(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                customer_email TEXT,
                context_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_last_activity 
            ON sessions(last_activity)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_email
            ON sessions(customer_email)
        """)
        self._conn.commit()
    
    def get(self, session_id: str) -> Optional[ConversationContext]:
        """Retrieve a session by ID."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT context_json FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        try:
            data = json.loads(row["context_json"])
            return ConversationContext(**data)
        except (json.JSONDecodeError, ValueError):
            return None
    
    def save(self, context: ConversationContext) -> None:
        """Save or update a session."""
        context.last_activity = datetime.utcnow()
        
        # Serialize context to JSON
        context_json = json.dumps(
            context.model_dump(),
            default=str  # Handle datetime serialization
        )
        
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sessions 
            (session_id, customer_email, context_json, created_at, last_activity)
            VALUES (?, ?, ?, ?, ?)
        """, (
            context.session_id,
            context.customer_email,
            context_json,
            context.created_at.isoformat(),
            context.last_activity.isoformat(),
        ))
        self._conn.commit()
    
    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0
    
    def cleanup_expired(self, max_age_minutes: int = 30) -> int:
        """Remove expired sessions."""
        cutoff = (datetime.utcnow() - timedelta(minutes=max_age_minutes)).isoformat()
        
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM sessions WHERE last_activity < ?",
            (cutoff,)
        )
        self._conn.commit()
        return cursor.rowcount
    
    def get_by_email(self, email: str) -> list[ConversationContext]:
        """Get all sessions for a customer email."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT context_json FROM sessions WHERE customer_email = ? ORDER BY last_activity DESC",
            (email,)
        )
        
        sessions = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row["context_json"])
                sessions.append(ConversationContext(**data))
            except (json.JSONDecodeError, ValueError):
                continue
        return sessions
    
    def get_recent_sessions(self, limit: int = 10) -> list[ConversationContext]:
        """Get most recent sessions."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT context_json FROM sessions ORDER BY last_activity DESC LIMIT ?",
            (limit,)
        )
        
        sessions = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row["context_json"])
                sessions.append(ConversationContext(**data))
            except (json.JSONDecodeError, ValueError):
                continue
        return sessions
    
    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
