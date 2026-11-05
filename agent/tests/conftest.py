"""
Pytest configuration — ensures the agent package is importable
and forces mock LLM / mock RAG for all tests.
"""

import os
import sys

# Ensure the parent directory is on sys.path so `agent` is importable
_AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _AGENT_DIR not in sys.path:
    sys.path.insert(0, _AGENT_DIR)

# Force mock LLM for all tests — must override the default (openai)
# so tests never make real API calls.
os.environ["LLM_PROVIDER"] = "mock"
