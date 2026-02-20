import os
from enum import Enum
from pathlib import Path

STATUS_FILE = Path(os.path.expanduser("~/.claude/claude-notifs-status.json"))

class Status(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    DONE = "done"
    ATTENTION = "attention"

# Priority order: higher index = higher priority
STATUS_PRIORITY = [Status.IDLE, Status.DONE, Status.WORKING, Status.ATTENTION]

EMOJI_MAP = {
    Status.IDLE: "⚪",
    Status.WORKING: "🔵",
    Status.DONE: "✅",
    Status.ATTENTION: "🟡",
}

# Seconds before a session is pruned entirely (safety net for stale entries)
SESSION_PRUNE_TIMEOUT = 86400  # 24 hours

# Menu bar poll interval in seconds
POLL_INTERVAL = 2
