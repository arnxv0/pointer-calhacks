import os
from typing import Optional, Dict, Any

from google.adk.tools import FunctionTool
import tzlocal  # pip install tzlocal

# Lazy imports so it won't crash if libs aren't installed yet
build = None
InstalledAppFlow = None
Credentials = None
Request = None

try:
    from googleapiclient.discovery import build  # type: ignore
except Exception:
    build = None
try:
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
    from google.oauth2.credentials import Credentials  # type: ignore
    from google.auth.transport.requests import Request  # type: ignore
except Exception:
    InstalledAppFlow = None
    Credentials = None

# Scopes and environment variables
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = os.environ.get("CALENDAR_ID", "primary")
OAUTH_CLIENT_PATH = os.environ.get("GOOGLE_CALENDAR_CREDENTIALS_JSON", "./client_secret.json")
TOKEN_PATH = os.environ.get("GOOGLE_CALENDAR_TOKEN_JSON", "./token.json")

# Default timezone (your case)
DEFAULT_TIMEZONE = os.environ.get("CALENDAR_TIMEZONE", "America/Los_Angeles")


def _build_service_oauth():
    """Authenticate with Google Calendar API using OAuth Installed App flow."""
    if not (build and InstalledAppFlow):
        raise RuntimeError(
            "Missing google-api-python-client or google-auth-oauthlib. "
            "Run: pip install google-api-python-client google-auth-oauthlib tzlocal"
        )

    creds = None
    if os.path.exists(TOKEN_PATH) and Credentials:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not OAUTH_CLIENT_PATH or not os.path.exists(OAUTH_CLIENT_PATH):
                raise RuntimeError(
                    f"OAuth client file not found at {OAUTH_CLIENT_PATH}. "
                    "Set GOOGLE_CALENDAR_CREDENTIALS_JSON to your client_secret.json."
                )
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())

    svc = build("calendar", "v3", credentials=creds)
    return svc


def _who_am_i_and_calendar(service, configured_calendar_id: str) -> Dict[str, Any]:
    """Identify which Google account and calendar are being used."""
    info: Dict[str, Any] = {}
    try:
        cl = service.calendarList().list(showHidden=True).execute()
        items = cl.get("items", [])
        primary = next((c for c in items if c.get("primary")), None)
        if primary:
            info["acting_email"] = primary.get("id")
            info["primary_calendar_id"] = primary.get("id")
            info["primary_summary"] = primary.get("summary")
    except Exception as e:
        info["identity_error"] = repr(e)

    if configured_calendar_id == "primary":
        info["resolved_calendar_id"] = info.get("primary_calendar_id", "primary")
    else:
        info["resolved_calendar_id"] = configured_calendar_id
    return info


async def add_to_calendar(
    title: str,
    start_iso: str,               # e.g. "2025-10-23T06:00:00"
    end_iso: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    time_zone: Optional[str] = None,
) -> dict:
    """
    Add an event to the signed-in user's Google Calendar (OAuth Installed App flow).
    Automatically adds timezone info.
    """
    tz = time_zone or os.environ.get("CALENDAR_TIMEZONE") or tzlocal.get_localzone_name() or DEFAULT_TIMEZONE

    payload = {
        "summary": title,
        "start": {"dateTime": start_iso, "timeZone": tz},
        "end": {"dateTime": end_iso or start_iso, "timeZone": tz},
        "description": description or "",
        "location": location or "",
    }

    try:
        service = _build_service_oauth()
    except Exception as e:
        return {
            "status": "dry_run",
            "reason": repr(e),
            "event": payload,
            "configured_calendar_id": CALENDAR_ID,
            "oauth_client_path": OAUTH_CLIENT_PATH,
            "token_path": TOKEN_PATH,
        }

    ident = _who_am_i_and_calendar(service, CALENDAR_ID)

    try:
        event = service.events().insert(
            calendarId=ident["resolved_calendar_id"],
            body=payload
        ).execute()

        creator = (event.get("creator") or {}).get("email")
        organizer = (event.get("organizer") or {}).get("email")

        return {
            "status": "success",
            "event_id": event.get("id"),
            "htmlLink": event.get("htmlLink"),
            "used_calendar_id": ident["resolved_calendar_id"],
            "acting_email": ident.get("acting_email"),
            "creator_email": creator,
            "organizer_email": organizer,
            "timezone_used": tz,
            "token_path": TOKEN_PATH,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": repr(e),
            "payload": payload,
            "resolved_calendar_id": ident.get("resolved_calendar_id"),
            "acting_email": ident.get("acting_email"),
            "token_path": TOKEN_PATH,
        }


# Register as ADK tool
CalendarTool = FunctionTool(func=add_to_calendar)
