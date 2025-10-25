from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional, Dict, Any, List
import json
import os
import asyncio
import logging

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
from cursor_manager import CursorManager
from ai_handler import AIHandler
from clipboard_manager import ClipboardManager
from keyboard_monitor import KeyboardMonitor
from screenshot_handler import ScreenshotHandler
from plugin_selector import PluginSelector

# Only import plugins if they exist
try:
    from plugins import get_plugin
    PLUGINS_AVAILABLE = True
except ImportError:
    PLUGINS_AVAILABLE = False
    print("⚠️  Plugins not available, running in basic mode")

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
cursor_mgr = CursorManager()
ai_handler = AIHandler()
clipboard_mgr = ClipboardManager()
screenshot_handler = ScreenshotHandler()

# KeyboardMonitor will be initialized in startup with access to active_connections
keyboard_monitor = None


class QueryRequest(BaseModel):
    query: str
    mode: str
    settings: Dict[str, Any]
    context: Optional[Dict[str, Any]] = {}


class PluginRequest(BaseModel):
    plugin_name: str
    context: Dict[str, Any]
    settings: Dict[str, Any]


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
async def execute_plugin(request: PluginRequest):
    """Execute a specific plugin"""
    if not PLUGINS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Plugins not available")
    
    try:
        plugin_class = get_plugin(request.plugin_name)
        
        if not plugin_class:
            raise HTTPException(status_code=404, detail=f"Plugin '{request.plugin_name}' not found")
        
        plugin = plugin_class(request.settings)
        
        if not plugin.is_enabled():
            raise HTTPException(status_code=400, detail=f"Plugin '{request.plugin_name}' not configured")
        
        result = await plugin.execute(request.context)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-query")
async def process_query(request: QueryRequest):
    """Process AI query with context-aware plugin detection"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 PROCESS QUERY CALLED")
        logger.info(f"📝 Original Query: {request.query}")
        logger.info(f"🔧 Mode: {request.mode}")
        logger.info(f"🔌 PLUGINS_AVAILABLE: {PLUGINS_AVAILABLE}")
        logger.info("=" * 60)
        
        mode = request.mode
        query = request.query.lower()
        settings = request.settings
        context = request.context
        
        # Add clipboard text to context
        context["clipboard_text"] = clipboard_mgr.paste()
        
        # If plugins are available, use AI to intelligently select the appropriate plugin
        if PLUGINS_AVAILABLE:
            logger.info("✅ Plugins are available, proceeding with plugin selection...")
            try:
                # Initialize AI-powered plugin selector
                api_key = settings.get("geminiApiKey")
                model = settings.get("geminiModel", "gemini-1.5-flash")
                
                if api_key:
                    logger.info("=" * 60)
                    logger.info("🤖 INITIALIZING PLUGIN SELECTOR")
                    logger.info(f"📝 Query: {request.query}")
                    logger.info(f"🔑 API Key present: {bool(api_key)}")
                    logger.info(f"🧠 Model: {model}")
                    logger.info("=" * 60)
                    
                    selector = PluginSelector(api_key, model)
                    
                    # Use AI to select the best plugin
                    logger.info("🔄 Calling selector.select_plugin()...")
                    plugin_name = await selector.select_plugin(request.query, context)
                    logger.info(f"✅ Selector returned: {plugin_name}")
                    
                    if plugin_name:
                        logger.info(f"🎯 FINAL DECISION: Using plugin '{plugin_name}'")
                        plugin_class = get_plugin(plugin_name)
                        
                        if plugin_class:
                            plugin = plugin_class(settings)
                            if plugin.is_enabled():
                                context["query"] = request.query
                                result = await plugin.execute(context)
                                return result
                            else:
                                logger.warning(f"⚠️  Plugin '{plugin_name}' not configured, falling back to general AI")
                        else:
                            logger.warning(f"⚠️  Plugin '{plugin_name}' not found, falling back to general AI")
                else:
                    logger.info("⚠️  No API key provided, skipping plugin selection")
            except Exception as e:
                logger.error(f"⚠️  Error in AI plugin selection: {e}, falling back to general AI")
        else:
            logger.info("⚠️  Plugins not available, using general AI handler")
        
        # Fallback to general AI response
        response = await ai_handler.process_query(
            query=request.query,
            mode=mode,
            api_key=settings.get("geminiApiKey"),
            model=settings.get("geminiModel", "gemini-1.5-flash")
        )
        
        if mode == "insert":
            await accessibility_mgr.replace_with_text(response, len(request.query))
        
        return {"success": True, "response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def save_settings(request: dict):
    try:
        settings = request.get("settings", request)
        with open("settings.json", "w") as f:
            json.dump(settings, f)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings")
async def load_settings():
    try:
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
            return settings
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "name": "Pointer Backend",
        "version": "1.0.0",
        "status": "running",
        "plugins_available": PLUGINS_AVAILABLE
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


def initialize_backend():
    """Initialize backend services before starting uvicorn"""
    global keyboard_monitor
    
    try:
        print("🚀 Pointer backend starting...", flush=True)
        
        # Initialize keyboard monitor with access to connection manager
        print("📡 Creating keyboard monitor...", flush=True)
        keyboard_monitor = KeyboardMonitor(connection_manager=connection_manager)
        
        print("⌨️  Starting keyboard monitor...", flush=True)
        keyboard_monitor.start()
        
        print("🖱️  Setting custom cursor...", flush=True)
        cursor_mgr.set_custom_cursor()
        
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
