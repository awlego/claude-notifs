"""macOS menu bar app showing Claude Code status.

Usage: python -m claude_notifs.menubar
"""

import subprocess

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
                pid = s.get("pid")
                callback = self._make_focus_callback(pid) if pid else None
                menu_items.append(rumps.MenuItem(label, callback=callback))
        else:
            menu_items.append(rumps.MenuItem("No active sessions"))

        # Replace menu contents (keep Quit button)
        self.menu.clear()
        for item in menu_items:
            self.menu.add(item)

    def _make_focus_callback(self, pid):
        """Create a callback that focuses the iTerm2 tab for the given PID."""
        def callback(_sender):
            self._focus_iterm_tab(pid)
        return callback

    def _focus_iterm_tab(self, pid):
        """Focus the iTerm2 tab containing the given PID."""
        try:
            result = subprocess.run(
                ["ps", "-o", "tty=", "-p", str(pid)],
                capture_output=True, text=True, timeout=5,
            )
            tty = result.stdout.strip()
            if not tty or tty == "??":
                return

            tty_path = f"/dev/{tty}"
            script = (
                'tell application "iTerm2"\n'
                "    repeat with w in windows\n"
                "        repeat with t in tabs of w\n"
                "            repeat with s in sessions of t\n"
                f'                if tty of s is "{tty_path}" then\n'
                "                    select t\n"
                "                    tell w to select\n"
                "                    activate\n"
                "                    return\n"
                "                end if\n"
                "            end repeat\n"
                "        end repeat\n"
                "    end repeat\n"
                "end tell\n"
            )
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, timeout=5,
            )
        except Exception:
            pass


def main():
    ClaudeStatusApp().run()


if __name__ == "__main__":
    main()
