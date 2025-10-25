from .base_plugin import BasePlugin
from typing import Dict, Any
import google.generativeai as genai
from datetime import datetime
import json
import webbrowser
import urllib.parse


class CalendarPlugin(BasePlugin):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract event details and add to Google Calendar"""
        event_text = context.get("selected_text", "")
        
        # Use AI to extract event details
        genai.configure(api_key=self.settings.get("geminiApiKey"))
        model = genai.GenerativeModel(self.settings.get("geminiModel", "gemini-1.5-flash"))
        
        prompt = f"""
        Extract event details from this text and format as JSON:
        {event_text}
        
        Return ONLY JSON with these fields:
        {{
            "title": "event title",
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "duration": "minutes as integer",
            "description": "event description"
        }}
        """
        
        response = model.generate_content(prompt)
        event_data = json.loads(response.text.strip().replace("``````", ""))
        
        # Create Google Calendar URL
        start_date = event_data["date"].replace("-", "")
        start_time = event_data["time"].replace(":", "") + "00"
        
        # Calculate end time
        start_dt = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M")
        from datetime import timedelta
        end_dt = start_dt + timedelta(minutes=event_data["duration"])
        end_time = end_dt.strftime("%Y%m%dT%H%M%S")
        start_time = start_dt.strftime("%Y%m%dT%H%M%S")
        
        calendar_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(event_data['title'])}&dates={start_time}/{end_time}&details={urllib.parse.quote(event_data['description'])}"
        
        # Open in browser
        webbrowser.open(calendar_url)
        
        return {
            "success": True,
            "message": "Calendar event opened in browser",
            "data": event_data
        }
    
    def is_enabled(self) -> bool:
        return bool(self.settings.get("geminiApiKey"))
