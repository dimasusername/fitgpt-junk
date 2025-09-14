"""
Test utilities and helper functions.
"""
import asyncio
from typing import Dict, Any


def run_async(coro):
    """Helper to run async functions in sync tests."""
    return asyncio.run(coro)


class MockDatabase:
    """Mock database for testing without real DB connection."""

    def __init__(self):
        self.data = {
            'conversations': [],
            'messages': [],
            'documents': [],
            'document_chunks': []
        }

    def table(self, name: str):
        """Mock table access."""
        return MockTable(self.data.get(name, []))


class MockTable:
    """Mock table for testing."""

    def __init__(self, data: list):
        self.data = data

    def select(self, *args, **kwargs):
        """Mock select operation."""
        return MockQuery(self.data)

    def insert(self, data: Dict[str, Any]):
        """Mock insert operation."""
        self.data.append(data)
        return MockQuery([data])


class MockQuery:
    """Mock query result."""

    def __init__(self, data: list):
        self.data = data
        self.count = len(data)

    def execute(self):
        """Mock execute."""
        return self

    def limit(self, n: int):
        """Mock limit."""
        return MockQuery(self.data[:n])
