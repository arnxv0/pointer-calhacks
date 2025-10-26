# Pointer - AI-Powered Cursor Assistant

Upgrade your mouse pointer to be agentic

Demo: https://youtu.be/ub4chFUHhtw

Tracks:

- Fetch.ai - Best use of Fetchai and ASI:One - the posisbilites with this are endless

- Ycombinator - Reimagining https://www.ycombinator.com/companies/raycast


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
- Python 3.8+ (Python 3.12 recommended)
- Node.js 18+
- npm or yarn

**Note**: Rust is automatically installed by Tauri CLI if not present.

## Quick Start (One Command!)

Clone the repository and run:

```bash
git clone <repository-url>
cd pointer
npm install
npm run tauri:dev
```

That's it! The build script will automatically:

- ✅ Create a Python virtual environment
- ✅ Install all Python dependencies
- ✅ Build the backend with PyInstaller
- ✅ Copy the binary to the correct location
- ✅ Start the app in development mode

## Installation (Detailed)

### 1. Clone and install npm dependencies

```bash
git clone <repository-url>
cd pointer
npm install
```

### 2. Run the app

```bash
npm run tauri:dev
```

The first run will take a few minutes as it sets up the Python environment and builds the backend.

### 3. Build for production (optional)

```bash
npm run tauri:build
```

This creates a single `.app` bundle in `src-tauri/target/release/bundle/macos/` with the Python backend automatically included.

## Manual Setup (Optional)

If you prefer to set up manually:

```bash
# Install npm dependencies
npm install

# Set up Python environment
cd src-python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Build and run
npm run tauri:dev
```

## Configuration

### Initial Setup

1. Launch the app with `npm run tauri:dev`
2. Click the gear icon (⚙️) to open Settings
3. Navigate to "Environment Variables"

### Required Configuration

**Google AI (Gemini)**

- Add `GOOGLE_API_KEY` in the "api_keys" category
- Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Mark as secret: Yes

**Email (Optional)**

- Category: "email"
- `SMTP_HOST`: Your SMTP server (e.g., smtp.gmail.com)
- `SMTP_PORT`: Usually 587
- `SMTP_USERNAME`: Your email address
- `SMTP_PASSWORD`: Your email password (mark as secret)
- `SMTP_FROM`: Sender email address

**Google Calendar (Optional)**

- Place your `credentials.json` from Google Cloud Console in `src-python/`
- Category: "calendar"
- The app will handle OAuth flow on first use

### Import Environment Variables

You can also import from a `.env` file:

1. Click "Import from .env"
2. Select your `.env` file
3. Variables are automatically categorized and encrypted

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
