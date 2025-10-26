# Disable Google ADK telemetry FIRST - must be before any Google ADK imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

from google.adk.agents import LlmAgent


TerminalCmdAgent = LlmAgent(
    name="TerminalCmdGen",
    model="gemini-2.5-flash",
    description="Generates safe terminal commands for tasks.",
    instruction="Generate ONLY the shell command, nothing else. No markdown, no code blocks, no comments, no explanations. Just the raw command. Never execute. Avoid destructive commands unless explicitly requested.",
    output_key="command",
)