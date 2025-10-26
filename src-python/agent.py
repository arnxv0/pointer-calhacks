# Disable Google ADK telemetry FIRST - must be before any Google ADK imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

import logging
from google.adk.agents import LlmAgent
from agents.coordinator import Coordinator

logger = logging.getLogger("pointer.agent")
logger.info("🚀 Initializing Pointer root agent...")

root_agent = LlmAgent(
    name="pointer_agent",
    model="gemini-2.5-flash",
    description="Multi-tool AI agent with context (image/video/text) + keyboard input.",
    instruction="""Intelligent AI assistant with knowledge base capabilities.

CORE CAPABILITIES:
1. Delegate tasks to appropriate agents
2. Use tools for: summarize, schedule, email, terminal commands, RAG queries
3. Automatically detect and handle knowledge base requests

KNOWLEDGE BASE MANAGEMENT:
- When user says "remember this", "save this", "add to knowledge base", "store this", etc.
- Automatically add the selected text or user's content to the knowledge base
- Use the RAG tool to store information for future retrieval
- Confirm when information is successfully stored

EXAMPLES:
User: "Remember this for later: Project deadline is December 15th"
→ Add to knowledge base and confirm

User: "Save this code snippet to my notes"
→ Store in knowledge base

User: "What did I save about the project deadline?"
→ Query knowledge base and retrieve information

Always be proactive in managing the knowledge base based on user intent.""",
    sub_agents=[Coordinator],
)

logger.info("✅ Pointer root agent initialized successfully")
