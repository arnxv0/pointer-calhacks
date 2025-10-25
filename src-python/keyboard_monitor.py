from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Controller as MouseController
import threading
import time
import asyncio


class KeyboardMonitor:
    def __init__(self, connection_manager=None):
        self.listener = None
        self.hotkey_callback = None
        self.current_keys = set()
        self.hotkey = {Key.cmd, Key.shift, KeyCode.from_char('k')}
        self.mouse = MouseController()
        self.connection_manager = connection_manager
        self.hotkey_active = False  # Debounce flag to prevent double triggers
        self.last_trigger_time = 0  # Track last trigger time for cooldown
        self.cooldown_seconds = 2  # Cooldown period in seconds
    
    def start(self):
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        print("⌨️  Keyboard monitor started")
    
    def stop(self):
        if self.listener:
            self.listener.stop()
    
    def _on_press(self, key):
        try:
            self.current_keys.add(key)
            
            # Check if hotkey combo is pressed, not already active, and cooldown has passed
            if self.current_keys >= self.hotkey and not self.hotkey_active:
                current_time = time.time()
                time_since_last_trigger = current_time - self.last_trigger_time
                
                if time_since_last_trigger >= self.cooldown_seconds:
                    self.hotkey_active = True
                    self.last_trigger_time = current_time
                    self._trigger_hotkey()
                else:
                    print(f"⏳ Hotkey cooldown active ({self.cooldown_seconds - time_since_last_trigger:.1f}s remaining)", flush=True)
        except Exception as e:
            print(f"❌ Error in _on_press: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    def _on_release(self, key):
        if key in self.current_keys:
            self.current_keys.remove(key)
        # Reset hotkey_active when any key is released
        if key in self.hotkey:
            self.hotkey_active = False
    
    def _trigger_hotkey(self):
        """Trigger hotkey and capture context"""
        try:
            print("\n" + "="*60, flush=True)
            print("🔥 HOTKEY TRIGGERED!", flush=True)
            print("="*60, flush=True)
            
            # Get mouse position
            print("📍 Getting mouse position...", flush=True)
            mouse_pos = self.mouse.position
            print(f"📍 Mouse position: {mouse_pos}", flush=True)
            
            # Get selected text using AppleScript (PyObjC accessibility causes crashes)
            print("📝 Getting selected text via AppleScript...", flush=True)
            try:
                import subprocess
                # Use AppleScript to copy selected text temporarily
                script = '''
                tell application "System Events"
                    keystroke "c" using command down
                end tell
                '''
                subprocess.run(['osascript', '-e', script], capture_output=True, timeout=1)
                # Small delay for clipboard to update
                time.sleep(0.1)
                # Get from clipboard
                from clipboard_manager import ClipboardManager
                clipboard = ClipboardManager()
                selected_text = clipboard.paste()
                print(f"📝 Selected text: {selected_text[:50]}..." if len(selected_text) > 50 else f"📝 Selected text: {selected_text}", flush=True)
            except Exception as e:
                print(f"⚠️  Could not get selected text: {e}", flush=True)
                selected_text = ""
            
            # Skip clipboard check - PyObjC pasteboard.types() causes fatal crash
            print("🖼️  Skipping clipboard check (PyObjC causes crashes)...", flush=True)
            has_screenshot = False
            
            # Send event to frontend via websocket or HTTP
            context = {
                "position": {"x": mouse_pos[0], "y": mouse_pos[1]},
                "selected_text": selected_text,
                "has_screenshot": has_screenshot,
                "timestamp": time.time()
            }

            print("📦 Context:", flush=True)
            print(context, flush=True)
            
            # Broadcast directly to all WebSocket connections
            print("📡 About to broadcast...", flush=True)
            self._broadcast_to_frontend(context)
            print("✅ Broadcast completed!", flush=True)
            
        except Exception as e:
            print(f"❌ Error in _trigger_hotkey: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    def _broadcast_to_frontend(self, context):
        """Broadcast hotkey event directly via WebSocket"""
        if not self.connection_manager:
            print("⚠️  No connection manager available!", flush=True)
            return
            
        conn_count = self.connection_manager.count()
        print(f"📡 Broadcasting to {conn_count} WebSocket connections", flush=True)
        
        if conn_count == 0:
            print("⚠️  No active WebSocket connections! Frontend not connected.", flush=True)
            return
            
        message = {
            "type": "hotkey-pressed",
            "data": context
        }
        
        print(f"📤 Sending message: {message}", flush=True)
        
        # Since we're in a different thread (pynput's thread), we need to schedule
        # the async operations in the main event loop
        import threading
        
        def send_to_all():
            """Send message to all connections"""
            connections = self.connection_manager.get_all()
            print(f"🔄 [WebSocket Thread] Starting send_to_all with {len(connections)} connections", flush=True)
            for i, connection in enumerate(connections):
                try:
                    print(f"📡 [WebSocket] Sending to connection {i+1}...", flush=True)
                    print(f"📡 [WebSocket] Creating new event loop...", flush=True)
                    loop = asyncio.new_event_loop()
                    print(f"📡 [WebSocket] Setting event loop...", flush=True)
                    asyncio.set_event_loop(loop)
                    print(f"📡 [WebSocket] Running send_json...", flush=True)
                    loop.run_until_complete(connection.send_json(message))
                    print(f"📡 [WebSocket] Closing loop...", flush=True)
                    loop.close()
                    print(f"✅ [WebSocket] Sent to connection {i+1}", flush=True)
                except Exception as e:
                    print(f"❌ [WebSocket] Failed to send to connection {i+1}: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
            print(f"🔄 [WebSocket Thread] Finished send_to_all", flush=True)
        
        # Run in a separate thread to avoid blocking the keyboard listener
        thread = threading.Thread(target=send_to_all, daemon=True)
        thread.start()
        
        print("="*60 + "\n", flush=True)
    
    def set_hotkey_callback(self, callback):
        self.hotkey_callback = callback
