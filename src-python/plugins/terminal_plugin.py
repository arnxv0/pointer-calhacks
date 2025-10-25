from .base_plugin import BasePlugin
from typing import Dict, Any
import google.generativeai as genai
import time


class TerminalPlugin(BasePlugin):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Convert natural language to terminal commands"""
        query = context.get("query", "")
        query_length = len(query)
        
        # Get AI response
        genai.configure(api_key=self.settings.get("geminiApiKey"))
        model = genai.GenerativeModel(self.settings.get("geminiModel", "gemini-1.5-flash"))
        
        prompt = f"""
        Convert this natural language query to a terminal command:
        {query}
        
        Return ONLY the command, no explanations or markdown formatting.
        """
        
        # Show thinking animation
        from accessibility import AccessibilityManager
        accessibility = AccessibilityManager()
        
        # Backspace the query
        for _ in range(query_length):
            accessibility.keyboard.press(accessibility.keyboard.Key.backspace)
            accessibility.keyboard.release(accessibility.keyboard.Key.backspace)
            time.sleep(0.01)
        
        # Type "thinking..."
        thinking = "thinking"
        accessibility.type_text(thinking)
        
        for i in range(3):
            accessibility.type_text(".")
            time.sleep(0.3)
        
        # Get AI response
        response = model.generate_content(prompt)
        command = response.text.strip()
        
        # Backspace "thinking..."
        for _ in range(len(thinking) + 3):
            accessibility.keyboard.press(accessibility.keyboard.Key.backspace)
            accessibility.keyboard.release(accessibility.keyboard.Key.backspace)
            time.sleep(0.01)
        
        # Type the command
        accessibility.type_text(command)
        
        return {
            "success": True,
            "command": command
        }
    
    def is_enabled(self) -> bool:
        return bool(self.settings.get("geminiApiKey"))
