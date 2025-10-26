# Disable Google ADK telemetry FIRST - must be before any Google ADK imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

import logging
from google.adk.agents import LlmAgent
from router import Coordinator

logger = logging.getLogger("pointer.agent")
logger.info("🚀 Initializing Pointer root agent...")

root_agent = LlmAgent(
    name="pointer_agent",
    model="gemini-2.5-flash",
    description="Multi-tool AI agent with context (image/video/text) + keyboard input.",
    instruction="Intelligent AI assistant. Delegate tasks to appropriate agents. Use tools for actions: summarize, schedule, email, terminal commands, or RAG queries.",
    sub_agents=[Coordinator],
)

logger.info("✅ Pointer root agent initialized successfully")
