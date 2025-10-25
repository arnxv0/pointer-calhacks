from .base_plugin import BasePlugin
from typing import Dict, Any
import google.generativeai as genai


class CodePlugin(BasePlugin):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix code errors with AI"""
        error_text = context.get("clipboard_text", "")
        query = context.get("query", "")
        
        # Generate fix
        genai.configure(api_key=self.settings.get("geminiApiKey"))
        model = genai.GenerativeModel(self.settings.get("geminiModel", "gemini-1.5-flash"))
        
        prompt = f"""
        Error/Code: {error_text}
        
        User query: {query}
        
        Provide the fixed code or solution.
        Return ONLY the code, no explanations or markdown formatting.
        """
        
        response = model.generate_content(prompt)
        fixed_code = response.text.strip().replace("```
        
        # Copy to clipboard
        from clipboard_manager import ClipboardManager
        clipboard = ClipboardManager()
        clipboard.copy(fixed_code)
        
        return {
            "success": True,
            "message": "Fixed code copied to clipboard",
            "fixed_code": fixed_code
        }
    
    def is_enabled(self) -> bool:
        return bool(self.settings.get("geminiApiKey"))
