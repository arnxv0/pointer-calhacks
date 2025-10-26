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
    description="Routes commands to tools. Email→send_email, Schedule→calendar, Summary→Summarizer, Terminal→TerminalCmdGen, Knowledge→RAG.",
    instruction=(
        "YOU MUST USE TOOLS DIRECTLY. Never delegate or transfer tasks. Execute actions immediately.\n\n"
        
        "You receive the user's spoken/typed command, plus any selected text from their screen.\n\n"
        
        "CALENDAR EVENTS (HIGHEST PRIORITY):\n"
        "When user says 'add to calendar', 'schedule', 'create event', 'add this event':\n"
        "1. Parse the selected text or user message for: title, date, time, location\n"
        "2. Convert to ISO 8601 format: YYYY-MM-DDTHH:MM:SS\n"
        "3. IMMEDIATELY call add_to_calendar(title, start_iso, end_iso, description, location)\n"
        "4. Use current date (October 25, 2025) as reference for 'tomorrow', 'Sunday', etc.\n"
        "5. Examples:\n"
        "   Selected text: 'Brunch 9:30 AM - 11:00 AM Sunday'\n"
        "   → add_to_calendar(title='Brunch', start_iso='2025-10-27T09:30:00', end_iso='2025-10-27T11:00:00')\n\n"
        
        "AUTOMATIC CONTEXT RETRIEVAL:\n"
        "- For ANY user question or request, FIRST query the knowledge base with rag_query() to find relevant stored information\n"
        "- Use the query results to enhance your response with personalized context\n"
        "- If relevant documents are found, incorporate them naturally into your answer\n\n"
        
        "EMAIL: When user wants to send an email, write a professional email using both their command and the selected text, then send it using send_email(to, subject, body).\n\n"
        
        "KNOWLEDGE BASE STORAGE:\n"
        "- Detect when user wants to remember/save/store information\n"
        "- Use rag_add(id, text, source) to store content\n"
        "- Confirm storage with a friendly message\n\n"
        
        "NEVER transfer to other agents. ALWAYS use tools directly.\n"
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
