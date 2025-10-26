# Google Calendar OAuth Setup

## Overview

Pointer uses Google OAuth 2.0 to securely connect to your Google Calendar. This allows you to create calendar events using voice commands without sharing your credentials.

## Setup Instructions

### 1. Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:

   - Click "Enable APIs and Services"
   - Search for "Google Calendar API"
   - Click "Enable"

4. Create OAuth credentials:

   - Go to "Credentials" in the sidebar
   - Click "+ CREATE CREDENTIALS"
   - Select "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Pointer Desktop"
   - Click "Create"

5. Download the credentials:
   - Click the download icon next to your new OAuth client ID
   - Save the file as `oauth_client_credentials.json`

### 2. Install the Credentials File

Place the `oauth_client_credentials.json` file in one of these locations:

- **macOS**: `~/Library/Application Support/Pointer/oauth_client_credentials.json`
- **Windows**: `%APPDATA%\Pointer\oauth_client_credentials.json`
- **Linux**: `~/.local/share/Pointer/oauth_client_credentials.json`

Alternatively, you can place it in the `src-python` directory for development.

### 3. Connect Your Calendar

1. Open Pointer
2. Go to Settings
3. Click on the "Calendar" tab
4. Click "Connect Google Calendar"
5. A browser window will open - sign in with your Google account
6. Grant Pointer permission to access your calendar
7. Close the browser window

That's it! You can now create calendar events with voice commands like:

- "Schedule a meeting tomorrow at 2pm"
- "Add 'Team standup' to my calendar every Monday at 9am"
- "Create a calendar event for lunch next Friday at noon"

## Security

- Your credentials are stored securely using OAuth 2.0
- Pointer only requests permission to manage calendar events
- You can revoke access at any time from [Google Account Permissions](https://myaccount.google.com/permissions)
- Tokens are stored locally in your application data directory

## Troubleshooting

### "OAuth client credentials not found"

Make sure the `oauth_client_credentials.json` file is in the correct location.

### "Failed to start OAuth flow"

Check that the Google Calendar API is enabled in your Google Cloud project.

### "Invalid grant" error

Your refresh token may have expired. Disconnect and reconnect your calendar in the settings.

## For Developers

The OAuth flow is implemented in `src-python/routes/calendar_auth.py`. Tokens are stored in:

- **macOS**: `~/Library/Application Support/Pointer/calendar_token.json`
- **Windows**: `%APPDATA%\Pointer\calendar_token.json`
- **Linux**: `~/.local/share/Pointer/calendar_token.json`
