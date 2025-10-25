try:
    from Cocoa import NSCursor, NSImage
except ImportError:
    print("Warning: PyObjC not available. Custom cursor will not work.")
    NSCursor = None
    NSImage = None

import os


class CursorManager:
    def __init__(self):
        self.custom_cursor = None
    
    def set_custom_cursor(self, svg_path: str = None):
        if NSCursor is None or NSImage is None:
            print("Custom cursor not available without PyObjC")
            return
        
        try:
            if not svg_path:
                svg_path = os.path.join(
                    os.path.dirname(__file__),
                    "../public/cursors/pointer.svg"
                )
            
            if os.path.exists(svg_path):
                image = NSImage.alloc().initWithContentsOfFile_(svg_path)
                
                if image:
                    cursor = NSCursor.alloc().initWithImage_hotSpot_(image, (0, 0))
                    cursor.set()
                    self.custom_cursor = cursor
                    print("✅ Custom cursor set successfully")
                else:
                    print("❌ Failed to load cursor image")
            else:
                print(f"❌ Cursor file not found: {svg_path}")
        
        except Exception as e:
            print(f"Error setting custom cursor: {e}")
    
    def reset_cursor(self):
        if NSCursor:
            NSCursor.arrowCursor().set()
