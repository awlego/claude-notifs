"""macOS menu bar app showing Claude Code status.

Usage: python -m claude_notifs.menubar
"""

import rumps

from .constants import EMOJI_MAP, POLL_INTERVAL, Status
from .status import get_active_sessions, read_status


class ClaudeStatusApp(rumps.App):
    def __init__(self):
        super().__init__("⚪ Claude", quit_button="Quit")
        self.timer = rumps.Timer(self.on_tick, POLL_INTERVAL)
        self.timer.start()

    def on_tick(self, _sender):
        data = read_status()
        sessions = data.get("sessions", {})
        active = get_active_sessions(sessions)

        # Build title: one emoji per active session
        if active:
            emojis = []
            for s in active.values():
                try:
                    s_emoji = EMOJI_MAP.get(Status(s.get("status", "idle")), "⚪")
                except ValueError:
                    s_emoji = "⚪"
                emojis.append(s_emoji)
            self.title = "".join(emojis)
        else:
            self.title = "⚪"

        # Build dropdown menu
        menu_items = []
        if active:
            for sid, s in active.items():
                s_status = s.get("status", "idle")
                try:
                    s_emoji = EMOJI_MAP.get(Status(s_status), "⚪")
                except ValueError:
                    s_emoji = "⚪"
                project = s.get("project", "unknown")
                msg = s.get("last_message", "")
                label = f"{s_emoji} {project}"
                if msg:
                    # Truncate for menu display
                    short_msg = msg[:80] + "..." if len(msg) > 80 else msg
                    label += f" - {short_msg}"
                menu_items.append(rumps.MenuItem(label))
        else:
            menu_items.append(rumps.MenuItem("No active sessions"))

        # Replace menu contents (keep Quit button)
        self.menu.clear()
        for item in menu_items:
            self.menu.add(item)


def main():
    ClaudeStatusApp().run()


if __name__ == "__main__":
    main()
