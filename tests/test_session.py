"""Tests for session management and multi-turn conversations."""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta

from src.memory.session_store import InMemorySessionStore, SQLiteSessionStore
from src.schemas.message import ConversationContext, CustomerMessage
from src.orchestrator import SupportOrchestrator


class TestInMemorySessionStore:
    """Test suite for in-memory session storage."""
    
    def test_save_and_get(self):
        """Test saving and retrieving a session."""
        store = InMemorySessionStore()
        
        context = ConversationContext(
            session_id="test-session-1",
            customer_email="test@example.com",
        )
        
        store.save(context)
        retrieved = store.get("test-session-1")
        
        assert retrieved is not None
        assert retrieved.session_id == "test-session-1"
        assert retrieved.customer_email == "test@example.com"
    
    def test_get_nonexistent(self):
        """Test getting a non-existent session."""
        store = InMemorySessionStore()
        result = store.get("nonexistent")
        assert result is None
    
    def test_delete(self):
        """Test deleting a session."""
        store = InMemorySessionStore()
        
        context = ConversationContext(session_id="to-delete")
        store.save(context)
        
        assert store.get("to-delete") is not None
        result = store.delete("to-delete")
        assert result is True
        assert store.get("to-delete") is None
    
    def test_delete_nonexistent(self):
        """Test deleting non-existent session."""
        store = InMemorySessionStore()
        result = store.delete("nonexistent")
        assert result is False
    
    def test_cleanup_expired(self):
        """Test cleanup of expired sessions."""
        store = InMemorySessionStore()
        
        # Create an "old" session by manipulating last_activity
        old_context = ConversationContext(session_id="old-session")
        old_context.last_activity = datetime.utcnow() - timedelta(minutes=60)
        store._sessions["old-session"] = old_context
        
        # Create a fresh session
        fresh_context = ConversationContext(session_id="fresh-session")
        store.save(fresh_context)
        
        # Cleanup with 30-minute threshold
        removed = store.cleanup_expired(max_age_minutes=30)
        
        assert removed == 1
        assert store.get("old-session") is None
        assert store.get("fresh-session") is not None


class TestSQLiteSessionStore:
    """Test suite for SQLite session storage."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_save_and_get(self, temp_db):
        """Test saving and retrieving a session."""
        store = SQLiteSessionStore(db_path=temp_db)
        
        context = ConversationContext(
            session_id="sqlite-test-1",
            customer_email="sqlite@example.com",
            verified_order_ids=["ORD-001", "ORD-002"],
        )
        context.messages.append({
            "role": "user",
            "content": "Hello",
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        store.save(context)
        retrieved = store.get("sqlite-test-1")
        
        assert retrieved is not None
        assert retrieved.session_id == "sqlite-test-1"
        assert retrieved.customer_email == "sqlite@example.com"
        assert len(retrieved.verified_order_ids) == 2
        assert len(retrieved.messages) == 1
        
        store.close()
    
    def test_persistence_across_instances(self, temp_db):
        """Test that sessions persist across store instances."""
        # Save with first instance
        store1 = SQLiteSessionStore(db_path=temp_db)
        context = ConversationContext(
            session_id="persistent-session",
            customer_email="persist@example.com",
        )
        store1.save(context)
        store1.close()
        
        # Retrieve with new instance
        store2 = SQLiteSessionStore(db_path=temp_db)
        retrieved = store2.get("persistent-session")
        
        assert retrieved is not None
        assert retrieved.customer_email == "persist@example.com"
        store2.close()
    
    def test_update_session(self, temp_db):
        """Test updating an existing session."""
        store = SQLiteSessionStore(db_path=temp_db)
        
        # Initial save
        context = ConversationContext(
            session_id="update-test",
            customer_email=None,
        )
        store.save(context)
        
        # Update
        context.customer_email = "updated@example.com"
        context.intent_history.append("order_status")
        store.save(context)
        
        # Verify
        retrieved = store.get("update-test")
        assert retrieved.customer_email == "updated@example.com"
        assert "order_status" in retrieved.intent_history
        
        store.close()
    
    def test_get_by_email(self, temp_db):
        """Test getting sessions by customer email."""
        store = SQLiteSessionStore(db_path=temp_db)
        
        # Create multiple sessions for same email
        for i in range(3):
            context = ConversationContext(
                session_id=f"email-test-{i}",
                customer_email="multi@example.com",
            )
            store.save(context)
        
        # Create session for different email
        other = ConversationContext(
            session_id="other-email",
            customer_email="other@example.com",
        )
        store.save(other)
        
        # Get by email
        sessions = store.get_by_email("multi@example.com")
        assert len(sessions) == 3
        
        store.close()
    
    def test_cleanup_expired(self, temp_db):
        """Test cleanup of expired sessions in SQLite."""
        store = SQLiteSessionStore(db_path=temp_db)
        
        # Create fresh session
        fresh = ConversationContext(session_id="fresh")
        store.save(fresh)
        
        # Manually insert old session with old timestamp
        import sqlite3
        conn = sqlite3.connect(temp_db)
        old_time = (datetime.utcnow() - timedelta(minutes=60)).isoformat()
        conn.execute("""
            INSERT OR REPLACE INTO sessions 
            (session_id, customer_email, context_json, created_at, last_activity)
            VALUES (?, ?, ?, ?, ?)
        """, ("old", None, '{"session_id": "old"}', old_time, old_time))
        conn.commit()
        conn.close()
        
        # Cleanup
        removed = store.cleanup_expired(max_age_minutes=30)
        
        assert removed >= 1
        assert store.get("old") is None
        assert store.get("fresh") is not None
        
        store.close()


class TestMultiTurnConversation:
    """Test suite for multi-turn conversation handling."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with in-memory storage for testing."""
        return SupportOrchestrator(use_persistent_storage=False)
    
    @pytest.mark.asyncio
    async def test_session_continuity(self, orchestrator):
        """Test that session maintains context across messages."""
        # First message with email
        msg1 = CustomerMessage(
            content="My email is alice.johnson@email.com",
            customer_email="alice.johnson@email.com",
        )
        response1 = await orchestrator.process(msg1)
        session_id = response1.session_id
        
        # Second message without email should use session context
        msg2 = CustomerMessage(
            content="Where is my order ORD-2024-002?",
            session_id=session_id,
        )
        response2 = await orchestrator.process(msg2, session_id)
        
        # Verify session continuity
        assert response2.session_id == session_id
        context = orchestrator.get_session(session_id)
        assert context is not None
        assert context.customer_email == "alice.johnson@email.com"
    
    @pytest.mark.asyncio
    async def test_order_id_remembered(self, orchestrator):
        """Test that order IDs are remembered in session."""
        # First message mentions an order
        msg1 = CustomerMessage(
            content="What's the status of ORD-2024-001?",
            customer_email="alice.johnson@email.com",
        )
        response1 = await orchestrator.process(msg1)
        session_id = response1.session_id
        
        # Verify order ID is stored
        context = orchestrator.get_session(session_id)
        assert "ORD-2024-001" in context.verified_order_ids
    
    @pytest.mark.asyncio
    async def test_intent_history_tracked(self, orchestrator):
        """Test that intent history is tracked."""
        # First message - order status
        msg1 = CustomerMessage(content="Where is my order?")
        response1 = await orchestrator.process(msg1)
        session_id = response1.session_id
        
        # Second message - refund
        msg2 = CustomerMessage(
            content="I want a refund",
            session_id=session_id,
        )
        await orchestrator.process(msg2, session_id)
        
        # Check intent history
        context = orchestrator.get_session(session_id)
        assert len(context.intent_history) >= 2
        assert "order_status" in context.intent_history
        assert "refund_request" in context.intent_history
    
    @pytest.mark.asyncio
    async def test_conversation_history_stored(self, orchestrator):
        """Test that conversation history is stored."""
        msg1 = CustomerMessage(content="Hello, I need help")
        response1 = await orchestrator.process(msg1)
        session_id = response1.session_id
        
        msg2 = CustomerMessage(
            content="Where is my order?",
            session_id=session_id,
        )
        await orchestrator.process(msg2, session_id)
        
        history = orchestrator.get_conversation_history(session_id)
        
        # Should have 4 messages (2 user + 2 assistant)
        assert len(history) >= 4
        assert any(m["role"] == "user" and "Hello" in m["content"] for m in history)
        assert any(m["role"] == "assistant" for m in history)
    
    @pytest.mark.asyncio
    async def test_follow_up_context_resolution(self, orchestrator):
        """Test resolution of follow-up messages with pronouns."""
        # First message establishes order context
        msg1 = CustomerMessage(
            content="What's the status of order ORD-2024-002?",
            customer_email="alice.johnson@email.com",
        )
        response1 = await orchestrator.process(msg1)
        session_id = response1.session_id
        
        # Get context and test follow-up resolution
        context = orchestrator.get_session(session_id)
        
        # Test pronoun resolution
        resolved = orchestrator.resolve_follow_up_context(
            "Can I refund it?",
            context
        )
        
        assert "order_id" in resolved
        assert resolved["order_id"] == "ORD-2024-002"
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, orchestrator):
        """Test session cleanup functionality."""
        # Create a session
        msg = CustomerMessage(content="Hello")
        response = await orchestrator.process(msg)
        session_id = response.session_id
        
        # Verify it exists
        assert orchestrator.get_session(session_id) is not None
        
        # Clear it
        result = orchestrator.clear_session(session_id)
        assert result is True
        
        # Verify it's gone
        assert orchestrator.get_session(session_id) is None
