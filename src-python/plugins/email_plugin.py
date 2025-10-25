from .base_plugin import BasePlugin
from typing import Dict, Any
import google.generativeai as genai
import webbrowser
import urllib.parse


class EmailPlugin(BasePlugin):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email and send via Gmail"""
        selected_text = context.get("selected_text", "")
        instruction = context.get("query", "")
        
        # Generate email with AI
        genai.configure(api_key=self.settings.get("geminiApiKey"))
        model = genai.GenerativeModel(self.settings.get("geminiModel", "gemini-1.5-flash"))
        
        prompt = f"""
        Context: {selected_text}
        
        Instruction: {instruction}
        
        Write a professional email. Return as JSON:
        {{
            "subject": "email subject",
            "body": "email body"
        }}
        """
        
        response = model.generate_content(prompt)
        import json
        email_data = json.loads(response.text.strip().replace("``````", ""))
        
        # Open Gmail compose with pre-filled content
        subject = urllib.parse.quote(email_data["subject"])
        body = urllib.parse.quote(email_data["body"])
        
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&su={subject}&body={body}"
        webbrowser.open(gmail_url)
        
        return {
            "success": True,
            "message": "Email draft opened in Gmail",
            "email": email_data
        }
    
    def is_enabled(self) -> bool:
        return bool(self.settings.get("geminiApiKey"))
