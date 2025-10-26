# Disable Google ADK telemetry FIRST - must be before any Google ADK imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

from google.adk.agents import LlmAgent


TerminalCmdAgent = LlmAgent(
    name="TerminalCmdGen",
    model="gemini-2.5-flash",
    description="Generates safe terminal commands for tasks.",
    instruction="Generate 1-3 shell commands with brief comments. Never execute. Avoid destructive commands unless explicitly requested.",
    output_key="command",
)