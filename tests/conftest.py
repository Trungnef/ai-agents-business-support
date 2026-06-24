"""Pytest configuration and fixtures."""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_data_cache():
    """Reset data cache before each test."""
    from src.tools.data_loader import DataLoader
    DataLoader.clear_cache()
    yield
    DataLoader.clear_cache()
