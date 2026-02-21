# claude-notifs

macOS menu bar status widget for Claude Code sessions.

Shows one color-coded emoji per active Claude Code session in your menu bar — e.g. `🔵🟡✅` for three sessions — so you can see the count and individual states at a glance:

| Emoji | Status | Meaning |
|-------|--------|---------|
| ⚪ | Idle | No active sessions / session idle |
| 🔵 | Working | Claude is generating a response |
| ✅ | Done | Claude finished responding |
| 🟡 | Attention | Permission prompt or notification waiting |

Clicking the menu bar icon shows a dropdown with per-session details.

## How it works

Two components:

1. **Hook** (`claude_notifs.hook`) — Called by Claude Code on lifecycle events (`SessionStart`, `UserPromptSubmit`, `Stop`, `Notification`, `PermissionRequest`). Writes session state to `~/.claude/claude-notifs-status.json`.

2. **Menu bar app** (`claude_notifs.menubar`) — A [rumps](https://github.com/jaredks/rumps) app that polls the status file every 2 seconds and updates the menu bar icon.

## Setup

### Install dependencies

```bash
cd /path/to/claude-notifs
uv venv env3.13 --python 3.13
uv pip install -e . --python env3.13/bin/python
```

### Configure the Claude Code hook

Add the hook to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/claude-notifs/env3.13/bin/python -m claude_notifs.hook"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/claude-notifs/env3.13/bin/python -m claude_notifs.hook"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/claude-notifs/env3.13/bin/python -m claude_notifs.hook"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/claude-notifs/env3.13/bin/python -m claude_notifs.hook"
          }
        ]
      }
    ],
    "PermissionRequest": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/claude-notifs/env3.13/bin/python -m claude_notifs.hook"
          }
        ]
      }
    ]
  }
}
```

Replace `/path/to/claude-notifs` with your actual install path.

### Run the menu bar app

#### Option A: Manual (foreground)

```bash
env3.13/bin/python -m claude_notifs.menubar
```

#### Option B: LaunchAgent (recommended)

A LaunchAgent runs the app automatically at login with no terminal window required.

Create `~/Library/LaunchAgents/com.yourname.claude-notifs.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yourname.claude-notifs</string>

    <key>ProgramArguments</key>
    <array>
        <string>/path/to/claude-notifs/env3.13/bin/python</string>
        <string>-m</string>
        <string>claude_notifs.menubar</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/path/to/claude-notifs</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/claude-notifs.stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/claude-notifs.stderr.log</string>
</dict>
</plist>
```

Replace `yourname` and `/path/to/claude-notifs` with your values.

#### Managing the LaunchAgent

```bash
# Load
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.yourname.claude-notifs.plist

# Restart (e.g. after code changes)
launchctl kickstart -k gui/$(id -u)/com.yourname.claude-notifs

# Stop
launchctl bootout gui/$(id -u)/com.yourname.claude-notifs

# Check status
launchctl list | grep claude-notifs
```

Logs are at `/tmp/claude-notifs.stdout.log` and `/tmp/claude-notifs.stderr.log`.
