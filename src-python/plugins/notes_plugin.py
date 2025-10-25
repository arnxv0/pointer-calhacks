from .base_plugin import BasePlugin
from typing import Dict, Any
import requests
import json


class NotesPlugin(BasePlugin):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Save selected text to Notion"""
        selected_text = context.get("selected_text", "")
        
        notion_token = self.settings.get("notionToken")
        notion_db_id = self.settings.get("notionDatabaseId")
        
        if not notion_token or not notion_db_id:
            return {"success": False, "message": "Notion not configured"}
        
        # Create Notion page
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        data = {
            "parent": {"database_id": notion_db_id},
            "properties": {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": f"Note - {selected_text[:50]}"
                            }
                        }
                    ]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": selected_text
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Saved to Notion",
                "page_id": response.json()["id"]
            }
        else:
            return {
                "success": False,
                "message": f"Failed: {response.text}"
            }
    
    def is_enabled(self) -> bool:
        return bool(self.settings.get("notionToken")) and bool(self.settings.get("notionDatabaseId"))
