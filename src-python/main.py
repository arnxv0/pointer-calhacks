# Disable ADK telemetry FIRST - must be before any Google ADK imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

# Monkey-patch telemetry to completely disable it
import sys
from unittest.mock import MagicMock
from functools import wraps

# Create a no-op decorator that preserves function signatures
def noop_decorator(*args, **kwargs):
    """A decorator that does nothing - just returns the function unchanged"""
    if len(args) == 1 and callable(args[0]) and not kwargs:
        # Called without arguments: @noop_decorator
        return args[0]
    else:
        # Called with arguments: @noop_decorator(...)
        def decorator(func):
            return func
        return decorator

# Create a fake telemetry module
fake_telemetry = MagicMock()
fake_telemetry.trace_call_llm = noop_decorator
sys.modules['google.adk.telemetry'] = fake_telemetry

print("🔇 Disabled Google ADK telemetry (avoids thought_signature bytes serialization issue)")

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional, Dict, Any, List
import json
import asyncio
import logging
import uuid

# Force load Quartz/PyObjC for pynput (required for PyInstaller)
try:
    import Quartz
    # Pre-load the functions that pynput needs
    _ = Quartz.CGEventGetIntegerValueField
    _ = Quartz.CGEventGetFlags
    _ = Quartz.CGEventGetType
except (ImportError, AttributeError) as e:
    print(f"⚠️  Warning: Could not preload Quartz functions: {e}")

# Set up logging
logger = logging.getLogger("pointer")
logger.setLevel(logging.INFO)

from accessibility import AccessibilityManager
from clipboard_manager import ClipboardManager
from keyboard_monitor import KeyboardMonitor
from screenshot_handler import ScreenshotHandler
from settings_manager import get_settings_manager

# Load environment variables from encrypted settings database
def load_env_from_settings():
    """Load environment variables from settings database into os.environ."""
    try:
        settings_mgr = get_settings_manager()
        all_settings = settings_mgr.get_all_settings(include_secrets=True, decrypt_secrets=True)
        
        # Load all settings into environment variables
        for category, settings in all_settings.items():
            for key, value in settings.items():
                if isinstance(value, str):
                    os.environ[key] = value
                    logger.info(f"Loaded {key} from settings database")
    except Exception as e:
        logger.warning(f"Could not load settings from database: {e}")
        # Fall back to .env file
        from dotenv import load_dotenv
        load_dotenv()

load_env_from_settings()

# Import Pointer backend agent
try:
    from agent import root_agent
    from google.adk.runners import InMemoryRunner
    from google.genai import types
    
    # Initialize the Pointer agent runner
    pointer_runner = InMemoryRunner(agent=root_agent, app_name="pointer_agent")
    POINTER_BACKEND_AVAILABLE = True
    print("✅ Pointer backend agent loaded successfully")
except ImportError as e:
    POINTER_BACKEND_AVAILABLE = False
    pointer_runner = None
    print(f"⚠️  Pointer backend not available: {e}, running in basic mode")

app = FastAPI(title="Pointer Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections in a class to ensure proper reference sharing
class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []
    
    def add(self, websocket: WebSocket):
        self.connections.append(websocket)
    
    def remove(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
    
    def get_all(self):
        return self.connections[:]
    
    def count(self):
        return len(self.connections)

connection_manager = ConnectionManager()

# Initialize managers
accessibility_mgr = AccessibilityManager()
clipboard_mgr = ClipboardManager()
screenshot_handler = ScreenshotHandler()

# KeyboardMonitor will be initialized in startup with access to active_connections
keyboard_monitor = None


# Pointer backend request/response models
class AgentRequest(BaseModel):
    message: str
    context_parts: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Startup event - keyboard monitor is initialized in main"""
    print("✅ Pointer backend startup event completed!")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time events"""
    await websocket.accept()
    connection_manager.add(websocket)
    print(f"✅ WebSocket connected! Total connections: {connection_manager.count()}")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📨 Received WebSocket message: {data}")
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        connection_manager.remove(websocket)
        print(f"❌ WebSocket disconnected. Remaining connections: {connection_manager.count()}")


@app.post("/api/execute-plugin")
async def execute_plugin(request: dict):
    """Legacy endpoint - no longer supported"""
    return {"success": False, "error": "Plugins removed - use /api/agent instead"}


@app.post("/api/process-query")
async def process_query(request: dict):
    """Legacy endpoint - converts old format to new /api/agent format"""
    try:
        query = request.get("query", "")
        context = request.get("context", {})
        
        # Convert to Pointer backend format
        agent_request = AgentRequest(
            message=query,
            context_parts=[
                {"type": "text", "content": f"Selected text: {context.get('selected_text', '')}"}
            ] if context.get('selected_text') else None,
            session_id=None
        )
        
        # Forward to Pointer backend
        result = await process_agent_request(agent_request)
        
        return {"success": True, "response": result.response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest):
    """
    Process user message through the Pointer agent and return results.
    
    Args:
        request: AgentRequest containing message, optional context, and session_id
    
    Returns:
        AgentResponse with agent's response and metadata
    """
    if not POINTER_BACKEND_AVAILABLE:
        raise HTTPException(status_code=503, detail="Pointer backend not available")
    
    try:
        logger.info("=" * 60)
        logger.info("🚀 POINTER AGENT REQUEST")
        logger.info(f"📝 Message: {request.message}")
        logger.info(f"🔑 Session ID: {request.session_id}")
        logger.info("=" * 60)
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        user_id = "default_user"
        
        # Create or get session
        session = pointer_runner.session_service.get_session(
            app_name=pointer_runner.app_name,
            user_id=user_id,
            session_id=session_id
        )
        if not session:
            session = pointer_runner.session_service.create_session(
                app_name=pointer_runner.app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        # Prepare the message content
        parts = [types.Part(text=request.message)]
        logger.info(f"📝 User message: {request.message}")
        print(f"[DEBUG] User message: {request.message}")
        
        # Add context parts if provided
        if request.context_parts:
            logger.info(f"📦 Context parts provided: {len(request.context_parts)} part(s)")
            print(f"[DEBUG] Context parts: {request.context_parts}")
            for idx, ctx_part in enumerate(request.context_parts):
                ctx_type = ctx_part.get("type")
                logger.info(f"   Part {idx+1}: type={ctx_type}")
                print(f"[DEBUG] Part {idx+1}: type={ctx_type}")
                if ctx_type == "text":
                    content = ctx_part.get("content", "")
                    logger.info(f"   Text content: {content[:100]}...")
                    print(f"[DEBUG] Text content: {content}")
                    parts.append(types.Part(text=content))
                elif ctx_type == "image":
                    # Handle base64 encoded images
                    import base64
                    mime_type = ctx_part.get("mime_type", "image/jpeg")
                    image_data = ctx_part.get("content")
                    if image_data:
                        logger.info(f"   Image: mime_type={mime_type}, size={len(image_data)} bytes")
                        print(f"[DEBUG] Image: mime_type={mime_type}, size={len(image_data)} bytes")
                        parts.append(types.Part(
                            inline_data=types.Blob(
                                mime_type=mime_type,
                                data=base64.b64decode(image_data)
                            )
                        ))
        else:
            logger.info("📦 No context parts provided")
            print("[DEBUG] No context parts")
        
        logger.info(f"📨 Total message parts: {len(parts)}")
        print(f"[DEBUG] Total message parts: {len(parts)}")
        new_message = types.Content(role="user", parts=parts)
        
        # Run the agent and collect the response
        logger.info("🤖 Starting agent execution...")
        print("[DEBUG] Starting agent execution...")
        response_text = ""
        event_count = 0
        async for event in pointer_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            event_count += 1
            logger.info(f"📊 Event {event_count}: {type(event).__name__}")
            print(f"[DEBUG] Event {event_count}: {type(event).__name__}")
            print(f"[DEBUG] Event content: {event.content if hasattr(event, 'content') else 'No content'}")
            
            # Collect the text from events
            if event.content and event.content.parts:
                logger.info(f"   Content parts: {len(event.content.parts)}")
                print(f"[DEBUG] Content parts count: {len(event.content.parts)}")
                for idx, part in enumerate(event.content.parts):
                    print(f"[DEBUG] Part {idx+1} type: {type(part).__name__}")
                    if hasattr(part, 'text') and part.text:
                        logger.info(f"   Part {idx+1} text: {part.text[:100]}...")
                        print(f"[DEBUG] Part {idx+1} text: {part.text}")
                        response_text += part.text
                    elif hasattr(part, 'function_call'):
                        logger.info(f"   Part {idx+1}: function_call detected")
                        print(f"[DEBUG] Part {idx+1}: function_call = {part.function_call}")
                    elif hasattr(part, 'thought_signature'):
                        logger.info(f"   Part {idx+1}: thought_signature (Gemini 2.5 feature)")
                        print(f"[DEBUG] Part {idx+1}: thought_signature detected")
                    elif hasattr(part, 'inline_data'):
                        logger.info(f"   Part {idx+1}: inline_data (binary content - skipping)")
                        print(f"[DEBUG] Part {idx+1}: inline_data detected (bytes - skipping)")
                    else:
                        logger.info(f"   Part {idx+1}: {type(part).__name__}")
                        print(f"[DEBUG] Part {idx+1}: unknown type {type(part).__name__}")
            else:
                logger.info("   No content in event")
                print("[DEBUG] Event has no content or no parts")
        
        logger.info(f"✅ Agent execution complete. Total events: {event_count}")
        print(f"[DEBUG] Agent execution complete. Total events: {event_count}")
        logger.info(f"✅ Final response length: {len(response_text)} chars")
        print(f"[DEBUG] Final response text: '{response_text}'")
        if response_text:
            logger.info(f"✅ Response preview: {response_text[:200]}...")
        
        result = AgentResponse(
            response=response_text or "Task completed successfully",
            session_id=session_id,
            metadata={"status": "success", "events": event_count}
        )
        print(f"[DEBUG] Returning AgentResponse: {result}")
        return result
    
    except Exception as e:
        logger.error(f"❌ Error in Pointer agent: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# Settings Management Endpoints

class SettingRequest(BaseModel):
    category: str
    key: str
    value: Any
    is_secret: bool = False
    description: Optional[str] = None


@app.get("/api/settings/categories")
async def get_settings_categories():
    """Get list of all setting categories."""
    try:
        settings_mgr = get_settings_manager()
        categories = settings_mgr.get_all_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/{category}")
async def get_category_settings(category: str, include_secrets: bool = False):
    """Get all settings in a category."""
    try:
        settings_mgr = get_settings_manager()
        settings = settings_mgr.get_category(
            category, 
            include_secrets=include_secrets,
            decrypt_secrets=False  # Never send decrypted secrets to frontend
        )
        return {"category": category, "settings": settings}
    except Exception as e:
        logger.error(f"Error getting category {category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/{category}/{key}")
async def get_setting(category: str, key: str):
    """Get a specific setting with metadata."""
    try:
        settings_mgr = get_settings_manager()
        value = settings_mgr.get(category, key, decrypt=False)
        info = settings_mgr.get_setting_info(category, key)
        
        if info is None:
            raise HTTPException(status_code=404, detail="Setting not found")
        
        return {
            "category": category,
            "key": key,
            "value": value,
            "info": info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting setting {category}.{key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def set_setting(request: SettingRequest):
    """Store a setting."""
    try:
        settings_mgr = get_settings_manager()
        success = settings_mgr.set(
            category=request.category,
            key=request.key,
            value=request.value,
            is_secret=request.is_secret,
            description=request.description
        )
        
        if success:
            return {
                "success": True,
                "message": f"Setting {request.category}.{request.key} saved successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save setting")
            
    except Exception as e:
        logger.error(f"Error saving setting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/settings/{category}/{key}")
async def delete_setting(category: str, key: str):
    """Delete a setting."""
    try:
        settings_mgr = get_settings_manager()
        success = settings_mgr.delete(category, key)
        
        if success:
            return {
                "success": True,
                "message": f"Setting {category}.{key} deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete setting")
            
    except Exception as e:
        logger.error(f"Error deleting setting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings/import")
async def import_settings(request: dict):
    """Import settings from .env format."""
    try:
        env_content = request.get("content", "")
        category = request.get("category", "imported")
        
        settings_mgr = get_settings_manager()
        count = settings_mgr.import_from_env(env_content, category)
        
        return {
            "success": True,
            "count": count,
            "message": f"Imported {count} settings"
        }
    except Exception as e:
        logger.error(f"Error importing settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/export/{category}")
async def export_settings(category: str):
    """Export settings as .env format."""
    try:
        settings_mgr = get_settings_manager()
        env_content = settings_mgr.export_to_env(category)
        
        return {
            "success": True,
            "content": env_content
        }
    except Exception as e:
        logger.error(f"Error exporting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "name": "Pointer Backend",
        "version": "1.0.0",
        "status": "running",
        "pointer_backend_available": POINTER_BACKEND_AVAILABLE
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "pointer_backend_available": POINTER_BACKEND_AVAILABLE}


# Hotkey Management Endpoints

class HotkeyConfig(BaseModel):
    modifiers: List[str]  # e.g., ["cmd", "shift"]
    key: str  # e.g., "k"


@app.get("/api/hotkey")
async def get_hotkey():
    """Get current hotkey configuration."""
    try:
        settings_mgr = get_settings_manager()
        hotkey_settings = settings_mgr.get_category("hotkey", include_secrets=False)
        
        # Return default if not configured
        if not hotkey_settings:
            return {
                "modifiers": ["cmd", "shift"],
                "key": "k"
            }
        
        return {
            "modifiers": hotkey_settings.get("modifiers", ["cmd", "shift"]),
            "key": hotkey_settings.get("key", "k")
        }
    except Exception as e:
        logger.error(f"Error getting hotkey: {e}")
        return {
            "modifiers": ["cmd", "shift"],
            "key": "k"
        }


@app.post("/api/hotkey")
async def set_hotkey(config: HotkeyConfig):
    """Set hotkey configuration and update the keyboard monitor."""
    try:
        # Validate modifiers
        valid_modifiers = ["cmd", "ctrl", "alt", "shift"]
        for mod in config.modifiers:
            if mod.lower() not in valid_modifiers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid modifier: {mod}. Must be one of {valid_modifiers}"
                )
        
        # Validate key (must be single character)
        if len(config.key) != 1:
            raise HTTPException(
                status_code=400,
                detail="Key must be a single character"
            )
        
        # Save to database
        settings_mgr = get_settings_manager()
        settings_mgr.set("hotkey", "modifiers", config.modifiers, is_secret=False,
                        description="Hotkey modifier keys")
        settings_mgr.set("hotkey", "key", config.key.lower(), is_secret=False,
                        description="Hotkey main key")
        
        # Update the keyboard monitor
        global keyboard_monitor
        if keyboard_monitor:
            hotkey_dict = {
                "modifiers": config.modifiers,
                "key": config.key.lower()
            }
            keyboard_monitor.update_hotkey(hotkey_dict)
        
        return {
            "success": True,
            "message": "Hotkey updated successfully",
            "hotkey": {
                "modifiers": config.modifiers,
                "key": config.key.lower()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting hotkey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hotkey/reset")
async def reset_hotkey():
    """Reset hotkey to default (Cmd+Shift+K)."""
    try:
        default_config = HotkeyConfig(
            modifiers=["cmd", "shift"],
            key="k"
        )
        return await set_hotkey(default_config)
    except Exception as e:
        logger.error(f"Error resetting hotkey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def initialize_backend():
    """Initialize backend services before starting uvicorn"""
    global keyboard_monitor
    
    try:
        print("🚀 Pointer backend starting...", flush=True)
        
        # Load hotkey configuration from database
        print("⌨️  Loading hotkey configuration...", flush=True)
        hotkey_config = None
        try:
            settings_mgr = get_settings_manager()
            hotkey_settings = settings_mgr.get_category("hotkey", include_secrets=False)
            
            if hotkey_settings and "modifiers" in hotkey_settings and "key" in hotkey_settings:
                hotkey_config = {
                    "modifiers": hotkey_settings["modifiers"],
                    "key": hotkey_settings["key"]
                }
                print(f"✅ Loaded hotkey: {hotkey_settings['modifiers']} + {hotkey_settings['key']}", flush=True)
            else:
                print("ℹ️  Using default hotkey: Cmd+Shift+K", flush=True)
        except Exception as e:
            print(f"⚠️  Could not load hotkey settings: {e}, using default", flush=True)
        
        # Initialize keyboard monitor with hotkey config
        print("📡 Creating keyboard monitor...", flush=True)
        keyboard_monitor = KeyboardMonitor(
            connection_manager=connection_manager,
            hotkey_config=hotkey_config
        )
        
        print("⌨️  Starting keyboard monitor...", flush=True)
        keyboard_monitor.start()
        
        print("🖱️  Loading cursor settings...", flush=True)
        # Load cursor settings from database
        # Note: The Tauri app should apply the cursor, not the Python backend
        try:
            settings_mgr = get_settings_manager()
            cursor_settings = settings_mgr.get_category("cursor", include_secrets=False)
            
            style = cursor_settings.get("style", "default")
            print(f"ℹ️  Cursor style in settings: {style}", flush=True)
            print(f"ℹ️  The Tauri frontend app should apply this cursor", flush=True)
        except Exception as e:
            print(f"⚠️  Could not load cursor settings: {e}", flush=True)
        
        print("✅ Pointer backend ready!", flush=True)
    except Exception as e:
        print(f"❌ Error initializing backend: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Initialize keyboard monitor before starting server
    initialize_backend()
    
    # When running as PyInstaller bundle, pass app object directly instead of module string
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765,
        log_level="info"
    )
