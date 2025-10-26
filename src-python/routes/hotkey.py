from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger("pointer.routes.hotkey")

router = APIRouter(prefix="/api/hotkey", tags=["hotkey"])

# Will be set by main.py
keyboard_monitor = None


class HotkeyConfig(BaseModel):
    keys: List[str]
    description: Optional[str] = None


@router.get("/current")
async def get_current_hotkey():
    """Get the current hotkey configuration."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        # Get hotkey from settings, default to Cmd+Shift+K
        hotkey_keys = settings_mgr.get("general", "hotkey_keys", decrypt_secret=False)
        if not hotkey_keys:
            hotkey_keys = ["cmd", "shift", "k"]
        
        description = settings_mgr.get("general", "hotkey_description", decrypt_secret=False)
        if not description:
            description = "Main hotkey"
        
        return {
            "keys": hotkey_keys,
            "description": description
        }
    except Exception as e:
        logger.error(f"Error getting hotkey: {e}")
        return {
            "keys": ["cmd", "shift", "k"],
            "description": "Main hotkey"
        }


@router.post("/set")
async def set_hotkey(config: HotkeyConfig):
    """Set a new hotkey configuration and update the keyboard monitor."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        # Validate keys
        if not config.keys or len(config.keys) < 1:
            raise HTTPException(status_code=400, detail="At least one key is required")
        
        # Save to database
        settings_mgr.set("general", "hotkey_keys", config.keys, is_secret=False, 
                        description="Hotkey keys combination")
        if config.description:
            settings_mgr.set("general", "hotkey_description", config.description, 
                           is_secret=False, description="Hotkey description")
        
        # Update the keyboard monitor
        if keyboard_monitor:
            success = keyboard_monitor.update_hotkey(config.keys)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update keyboard monitor")
        
        return {
            "success": True,
            "keys": config.keys,
            "description": config.description,
            "message": "Hotkey updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting hotkey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_hotkey():
    """Reset hotkey to default (Cmd+Shift+K)."""
    try:
        from utils.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        
        default_keys = ["cmd", "shift", "k"]
        
        # Save to database
        settings_mgr.set("general", "hotkey_keys", default_keys, is_secret=False)
        settings_mgr.set("general", "hotkey_description", "Main hotkey", is_secret=False)
        
        # Update the keyboard monitor
        if keyboard_monitor:
            keyboard_monitor.update_hotkey(default_keys)
        
        return {
            "success": True,
            "keys": default_keys,
            "description": "Main hotkey",
            "message": "Hotkey reset to default"
        }
    except Exception as e:
        logger.error(f"Error resetting hotkey: {e}")
        raise HTTPException(status_code=500, detail=str(e))
