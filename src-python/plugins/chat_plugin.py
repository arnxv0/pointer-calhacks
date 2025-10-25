from .base_plugin import BasePlugin
from typing import Dict, Any
import google.generativeai as genai
import time


class ChatPlugin(BasePlugin):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate witty replies for chats"""
        chat_context = context.get("selected_text", "")
        query = context.get("query", "")
        query_length = len(query)
        
        # Generate witty reply
        genai.configure(api_key=self.settings.get("geminiApiKey"))
        model = genai.GenerativeModel(self.settings.get("geminiModel", "gemini-1.5-flash"))
        
        prompt = f"""
        Chat context: {chat_context}
        
        User wants: {query}
        
        Generate a witty, charming reply that fits the conversation.
        Keep it natural and conversational.
        Return ONLY the reply text, nothing else.
        """
        
        from accessibility import AccessibilityManager
        accessibility = AccessibilityManager()
        
        # Backspace the query
        for _ in range(query_length):
            accessibility.keyboard.press(accessibility.keyboard.Key.backspace)
            accessibility.keyboard.release(accessibility.keyboard.Key.backspace)
            time.sleep(0.01)
        
        # Show thinking animation
        thinking = "thinking"
        accessibility.type_text(thinking)
        
        for i in range(3):
            accessibility.type_text(".")
            time.sleep(0.3)
        
        # Get response
        response = model.generate_content(prompt)
        reply = response.text.strip()
        
        # Backspace thinking
        for _ in range(len(thinking) + 3):
            accessibility.keyboard.press(accessibility.keyboard.Key.backspace)
            accessibility.keyboard.release(accessibility.keyboard.Key.backspace)
            time.sleep(0.01)
        
        # Type reply
        accessibility.type_text(reply)
        
        return {
            "success": True,
            "reply": reply
        }
    
    def is_enabled(self) -> bool:
        return bool(self.settings.get("geminiApiKey"))
