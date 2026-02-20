"""Claude Code hook entry point.

Called by Claude Code on lifecycle events. Reads JSON from stdin,
writes session state to the shared status file.

Usage: python -m claude_notifs.hook
"""

import json
import os
import sys

from .constants import Status
from .status import write_session_status

# Map hook event names to statuses
EVENT_STATUS_MAP = {
    "SessionStart": Status.IDLE,
    "UserPromptSubmit": Status.WORKING,
    "Stop": Status.DONE,
    "Notification": Status.ATTENTION,
    "PermissionRequest": Status.ATTENTION,
}


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    event = data.get("hook_event_name", "")
    session_id = data.get("session_id", "")
    if not session_id:
        sys.exit(0)

    status = EVENT_STATUS_MAP.get(event)
    if status is None:
        sys.exit(0)

    cwd = data.get("cwd", "")
    project = os.path.basename(cwd) if cwd else "unknown"

    # Extract a useful message depending on the event
    last_message = ""
    if event == "Stop":
        last_message = data.get("stop_hook_data", {}).get("response", "")
        # Truncate long messages
        if len(last_message) > 200:
            last_message = last_message[:200] + "..."
    elif event == "Notification":
        last_message = data.get("notification", {}).get("message", "")
    elif event == "PermissionRequest":
        tool = data.get("permission_request", {}).get("tool_name", "")
        last_message = f"Permission needed: {tool}" if tool else "Permission needed"

    # The hook is a child of the Claude Code process, so getppid() gives us its PID
    pid = os.getppid()

    write_session_status(
        session_id=session_id,
        status=status.value,
        project=project,
        cwd=cwd,
        last_message=last_message,
        pid=pid,
    )


if __name__ == "__main__":
    main()
