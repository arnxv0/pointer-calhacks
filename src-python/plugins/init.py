from .calendar_plugin import CalendarPlugin
from .slack_plugin import SlackPlugin
from .terminal_plugin import TerminalPlugin
from .email_plugin import EmailPlugin
from .notes_plugin import NotesPlugin
from .screenshot_plugin import ScreenshotPlugin
from .chat_plugin import ChatPlugin
from .code_plugin import CodePlugin

PLUGINS = {
    "calendar": CalendarPlugin,
    "slack": SlackPlugin,
    "terminal": TerminalPlugin,
    "email": EmailPlugin,
    "notes": NotesPlugin,
    "screenshot": ScreenshotPlugin,
    "chat": ChatPlugin,
    "code": CodePlugin,
}

def get_plugin(name: str):
    return PLUGINS.get(name)
