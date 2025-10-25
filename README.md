# Pointer - AI-Powered Cursor Assistant

A macOS desktop application that enhances your cursor with AI capabilities.

## Features

- 🎯 Custom cursor with beautiful SVG design
- ⌨️ Global hotkey support for text selection
- 🖼️ Screenshot analysis with AI
- 💬 Inline query mode with intelligent typing
- 🔌 Plugin system for custom integrations
- 🤖 Powered by Google Gemini AI

### Available Plugins

1. **Calendar Integration** - Add events to Google Calendar
2. **Database Query** - Query databases and generate visualizations
3. **Terminal Assistant** - Generate terminal commands
4. **Email Generator** - Generate and send emails via Gmail
5. **Notes Saver** - Save to Notion, Excel, or text files
6. **Screenshot Explainer** - Explain screenshots with AI
7. **Chat Assistant** - Generate witty chat replies
8. **Code Helper** - Fix code errors and bugs
9. **RAG Document Index** - Index and search your documents

## Prerequisites

- macOS 12.0 or later
- Python 3.9+
- Node.js 18+
- Rust (for Tauri)
- Gemini API Key

## Installation

### 1. Install dependencies

```bash
npm install
cd src-python && pip install -r requirements.txt && cd ..
```

### 2. Build Python backend

```bash
cd src-python && python build.py && cd ..
```

This creates a platform-specific binary (e.g., `pointer-backend-aarch64-apple-darwin` on Apple Silicon Macs).

### 3. Copy binary to Tauri

```bash
mkdir -p src-tauri/binaries
cp src-python/dist/pointer-backend-* ../src-tauri/binaries/
```

### 4. Run in development

```bash
npm run tauri:dev
```

### 5. Build for production

```bash
npm run tauri:build
```

This creates a single `.app` bundle in `src-tauri/target/release/bundle/macos/` with the Python backend automatically included.

## Configuration

1. Open the app
2. Navigate to "AI Configuration"
3. Enter your Gemini API key
4. Customize hotkeys in "Hotkey Configuration"

## Usage

### Text Selection Mode

1. Select any text
2. Press `⌘+Shift+K`
3. Type your query
4. AI processes and responds

### Screenshot Mode

1. Take a screenshot (⌘+Shift+4)
2. Press `⌘+Shift+K`
3. Ask questions about the image

### Inline Mode

1. Focus any text field
2. Press `⌘+Shift+K`
3. Type your query
4. AI types the response

## Architecture

The app uses a clean separation of concerns:

- **Python Backend**: Handles keyboard monitoring, accessibility APIs, AI processing, and plugin execution
- **Tauri**: Manages native windows and bundles the Python backend as a sidecar process
- **React Frontend**: Renders the UI and communicates with the backend via HTTP/WebSocket

## License

MIT

USER PRESSES ⌘+Shift+K
↓
Python Keyboard Monitor (keyboard_monitor.py)
↓
Captures Context
(position, text, screenshot)
↓
POST /api/hotkey-triggered ← HTTP → Python Backend (main.py)
↓
WebSocket Broadcast
↓
React Frontend (App.tsx) ← WebSocket
↓
invoke('show_overlay') → Tauri (main.rs)
↓
Creates Overlay Window
at cursor position
↓
User types query + Enter
↓
POST /api/process-query ← HTTP → Python Backend (main.py)
↓
AI Plugin Selector
(plugin_selector.py)
↓
Plugin Execution OR
General AI Handler
↓
Response returns to Frontend
↓
Shows success message
↓
Auto-closes after 2s

cd src-python && python3 build.py && cp dist/pointer-backend-aarch64-apple-darwin ../src-tauri/binaries/
