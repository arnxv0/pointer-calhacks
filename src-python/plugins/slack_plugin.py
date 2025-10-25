from .base_plugin import BasePlugin
from typing import Dict, Any
import google.generativeai as genai
import matplotlib.pyplot as plt
import io
import base64
from PIL import ImageGrab
import time


class SlackPlugin(BasePlugin):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Query database and generate graph for transaction failures"""
        query = context.get("query", "")
        
        # Use AI to generate SQL query and graph code
        genai.configure(api_key=self.settings.get("geminiApiKey"))
        model = genai.GenerativeModel(self.settings.get("geminiModel", "gemini-1.5-flash"))
        
        prompt = f"""
        User query: {query}
        
        Generate Python code to:
        1. Query a PostgreSQL database for transaction failure data
        2. Create a matplotlib graph
        3. Return the code as a string
        
        Assume database connection is available as `conn`.
        Return ONLY the Python code, no explanations.
        """
        
        # Show "thinking..." animation
        from accessibility import AccessibilityManager
        accessibility = AccessibilityManager()
        
        await self._show_thinking(accessibility)
        
        response = model.generate_content(prompt)
        code = response.text.strip().replace("``````", "")
        
        # Execute code to generate graph (in production, use proper DB connection)
        # For demo, create sample graph
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot([1, 2, 3, 4, 5], [10, 15, 13, 17, 20])
        ax.set_title("Transaction Failures Over Time")
        ax.set_xlabel("Day")
        ax.set_ylabel("Failures")
        
        # Save to clipboard as image
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        
        from PIL import Image
        img = Image.open(buf)
        
        # Copy to clipboard
        from clipboard_manager import ClipboardManager
        clipboard = ClipboardManager()
        clipboard.copy_image(img)
        
        # Paste it
        accessibility.paste()
        
        return {
            "success": True,
            "message": "Graph generated and pasted"
        }
    
    async def _show_thinking(self, accessibility):
        """Show 'thinking...' with animated dots"""
        thinking_text = "thinking"
        accessibility.type_text(thinking_text)
        
        for _ in range(3):
            accessibility.type_text(".")
            time.sleep(0.3)
            accessibility.keyboard.press(accessibility.keyboard.Key.backspace)
            accessibility.keyboard.release(accessibility.keyboard.Key.backspace)
    
    def is_enabled(self) -> bool:
        return bool(self.settings.get("geminiApiKey"))
