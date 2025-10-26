import os
from google.adk.agents import LlmAgent
from .router import Coordinator


root_agent = LlmAgent(
    name="pointer_agent",
    model="gemini-2.0-flash",
    description="Pointer: a multi-tool AI agent with context (image/video/text) + keyboard command input.",
    instruction=("""
    You are Pointer, an intelligent AI assistant. You receive a user command and optional context.
    Always delegate the task to the appropriate agent. Use your best judgement 
    to determine which agent to delegate to.

    Use your tools to summarize, schedule, email, generate terminal commands, or answer via RAG.
    If there is no appropriate tool you can give a generic response.
    """),
    sub_agents=[Coordinator],
)
