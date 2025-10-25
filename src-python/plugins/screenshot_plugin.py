from .base_plugin import BasePlugin
from typing import Dict, Any
import google.generativeai as genai
from PIL import Image
import io


class ScreenshotPlugin(BasePlugin):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Explain screenshot using AI vision"""
        screenshot_data = context.get("screenshot")
        
        if not screenshot_data:
            return {"success": False, "message": "No screenshot found"}
        
        # Use Gemini Vision to analyze
        genai.configure(api_key=self.settings.get("geminiApiKey"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Convert screenshot to PIL Image
        image = Image.open(io.BytesIO(screenshot_data))
        
        response = model.generate_content([
            "Explain what's in this image in detail. Describe all visible elements, text, and context.",
            image
        ])
        
        explanation = response.text
        
        return {
            "success": True,
            "explanation": explanation
        }
    
    def is_enabled(self) -> bool:
        return bool(self.settings.get("geminiApiKey"))
