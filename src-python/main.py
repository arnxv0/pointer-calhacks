# Disable ADK telemetry FIRST - must be before any Google ADK imports
import os
os.environ["GOOGLE_ADK_DISABLE_TELEMETRY"] = "1"

# Monkey-patch telemetry to completely disable it
import sys
from unittest.mock import MagicMock

# Create a no-op decorator that preserves function signatures
def noop_decorator(*args, **kwargs):
    """A decorator that does nothing - just returns the function unchanged"""
    if len(args) == 1 and callable(args[0]) and not kwargs:
        return args[0]
    else:
        def decorator(func):
            return func
        return decorator

# Create a fake telemetry module
fake_telemetry = MagicMock()
fake_telemetry.trace_call_llm = noop_decorator
sys.modules['google.adk.telemetry'] = fake_telemetry

print("🔇 Disabled Google ADK telemetry (avoids thought_signature bytes serialization issue)")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List
import logging

# Force load Quartz/PyObjC for pynput (required for PyInstaller)
try:
    import Quartz
    _ = Quartz.CGEventGetIntegerValueField
    _ = Quartz.CGEventGetFlags
    _ = Quartz.CGEventGetType
except (ImportError, AttributeError) as e:
    print(f"⚠️  Warning: Could not preload Quartz functions: {e}")

# Set up logging
logger = logging.getLogger("pointer")
logger.setLevel(logging.INFO)

from utils import (
    AccessibilityManager,
    ClipboardManager,
    KeyboardMonitor,
    ScreenshotHandler,
    get_settings_manager
)

# Load environment variables from encrypted settings database
def load_env_from_settings():
    """Load environment variables from settings database into os.environ."""
    try:
        settings_mgr = get_settings_manager()
        all_settings = settings_mgr.get_all_settings(include_secrets=True, decrypt_secrets=True)
        
        for category, settings in all_settings.items():
            for key, value in settings.items():
                if isinstance(value, str):
                    os.environ[key] = value
                    logger.info(f"Loaded {key} from settings database")
    except Exception as e:
        logger.warning(f"Could not load settings from database: {e}")
        from dotenv import load_dotenv
        load_dotenv()

load_env_from_settings()

# Import Pointer backend agent
try:
    from agent import root_agent
    from google.adk.runners import InMemoryRunner
    
    pointer_runner = InMemoryRunner(agent=root_agent, app_name="pointer_agent")
    POINTER_BACKEND_AVAILABLE = True
    print("✅ Pointer backend agent loaded successfully")
except ImportError as e:
    POINTER_BACKEND_AVAILABLE = False
    pointer_runner = None
    print(f"⚠️  Pointer backend not available: {e}, running in basic mode")

# Create FastAPI app
app = FastAPI(title="Pointer Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from routes import health, settings, hotkey, rag, agent, storage, calendar_auth, asi

# Set the POINTER_BACKEND_AVAILABLE flag in health router
health.POINTER_BACKEND_AVAILABLE = POINTER_BACKEND_AVAILABLE

# Set the pointer_runner in agent router
agent.pointer_runner = pointer_runner

# Include all route modules
app.include_router(health.router)
app.include_router(settings.router)
app.include_router(hotkey.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(storage.router)
app.include_router(calendar_auth.router)
app.include_router(asi.router, prefix="/api/asi", tags=["asi"])

# WebSocket connection manager
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

# Global keyboard monitor instance
keyboard_monitor = None


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
    except WebSocketDisconnect:
        connection_manager.remove(websocket)
        print(f"❌ WebSocket disconnected. Remaining connections: {connection_manager.count()}")


def get_keyboard_monitor():
    """Get the global keyboard monitor instance"""
    return keyboard_monitor


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
        
        # Make keyboard_monitor available to hotkey router
        hotkey.keyboard_monitor = keyboard_monitor
        
        print("✅ Pointer backend ready!", flush=True)
    except Exception as e:
        print(f"❌ Error initializing backend: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Initialize keyboard monitor before starting server
    initialize_backend()
    
    # Run uvicorn server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765,
        log_level="info"
    )
