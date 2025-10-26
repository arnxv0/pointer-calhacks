# Disable Google ADK telemetry FIRST - must be before any Google ADK imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

import logging
from google.adk.agents import LlmAgent
from agents.summarize import SummarizerAgent
from agents.terminal_cmd import TerminalCmdAgent
from tools.calendar import CalendarTool
from tools.emailer import EmailTool
from tools.rag import RagAddTool, RagQueryTool
from tools.vision import AttachContextTool , ListContextHelpTool

logger = logging.getLogger("pointer.router")
logger.info("🎯 Initializing Coordinator agent...")
print("[DEBUG ROUTER] Initializing Coordinator agent...")

Coordinator = LlmAgent(
    name="PointerCoordinator",
    model="gemini-2.5-flash",
    description="Routes commands to tools. Email→send_email, Schedule→calendar, Summary→Summarizer, Terminal→TerminalCmdGen.",
    instruction=(
        "Route commands to tools. Use tools directly - never ask for information.\n\n"
        
        "You receive the user's spoken/typed command, plus any selected text from their screen.\n\n"
        
        "When user wants to send an email, write a professional email using both their command and the selected text, then send it using send_email(to, subject, body).\n"
    ),
    tools=[
        CalendarTool,
        EmailTool,
        RagAddTool,
        RagQueryTool,
        AttachContextTool,
        ListContextHelpTool,
    ],
    sub_agents=[
        SummarizerAgent,
        TerminalCmdAgent,
    ],
)

logger.info("✅ Coordinator agent initialized successfully")
logger.info(f"   Tools: {len(Coordinator.tools)} tool(s)")
logger.info(f"   Sub-agents: {len(Coordinator.sub_agents)} sub-agent(s)")
print(f"[DEBUG ROUTER] Coordinator initialized with {len(Coordinator.tools)} tools and {len(Coordinator.sub_agents)} sub-agents")
