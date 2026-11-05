"""
Prohor Agent — AI-powered legal literacy assistant for Bangladeshi citizens.

Public API:
    from agent import invoke_agent, AgentRequest, AgentResponse

The entry point is ``invoke_agent(request)`` which accepts an
``AgentRequest`` and returns an ``AgentResponse``.
"""

from agent.entry_point import invoke_agent
from agent.schemas.request import AgentRequest
from agent.schemas.response import AgentResponse

__all__ = ["invoke_agent", "AgentRequest", "AgentResponse"]
