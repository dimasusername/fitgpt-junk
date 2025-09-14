"""
Test configuration and shared fixtures for the FastAPI server tests.
"""
import sys
from pathlib import Path

# Add the server root to Python path so we can import app modules
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))
