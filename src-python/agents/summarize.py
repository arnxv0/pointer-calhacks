# Disable Google ADK telemetry FIRST - must be before any Google ADK imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

from google.adk.agents import LlmAgent

SummarizerAgent = LlmAgent(
    name="Summarizer",
    model="gemini-2.5-flash",
    description="Summarizes text, images, or documents.",
    instruction="Crisp summarizer. Use context_parts if present. Output 3-7 bullets. Be faithful and specific.",
    output_key="summary",
)
