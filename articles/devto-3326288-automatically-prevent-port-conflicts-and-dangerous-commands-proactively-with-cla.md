---
title: "Automatically Prevent Port Conflicts and Dangerous Commands Proactively with Claude Code's Hooks Feature"
date: 2026-03-08
topics: ["devtools", "python", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/claude-code-hooks"
devto_url: "https://dev.to/soytuber/automatically-prevent-port-conflicts-and-dangerous-commands-proactively-with-claude-codes-hooks-5256"
devto_id: 3326288
---

## What are Claude Code hooks?

Claude Code's hooks feature enables event-driven automation before and after tool execution. It supports multiple lifecycle events such as PreToolUse (pre-execution validation), PostToolUse (post-execution processing), and UserPromptSubmit (on prompt submission). By enforcing rules in advance, it enhances development safety. The PreToolUse hook, in particular, is suitable for pre-execution validation and blocking.

## How the PreToolUse hook works

The PreToolUse hook automatically executes validation logic before tool execution. Scripts registered in .claude/settings.json perform validation before a command is run.

The execution flow is as follows:

1.  The user enters `python app.py --port 8000`
2.  Claude Code triggers the PreToolUse hook
3.  The registered script parses the command content and determines if port 8000 is in use
4.  If in use, the command execution is blocked

## Implementing a Port Conflict Prevention Script

```bash
# check-port.py
import json
import re
import psutil
import sys

def main(command):
    # コマンドからポート番号を抽出
    match = re.search(r'--port\s+(\d+)', command)
    if not match:
        return json.dumps({"result": "allow", "message": "Port not specified"})

    port = int(match.group(1))
    # 使用中のポートをスキャン
    for conn in psutil.net_connections():
        if conn.laddr and conn.laddr.port == port:
            return json.dumps({
                "result": "deny",
                "message": f"Port {port} is already in use by PID {conn.pid}",
                "pid": conn.pid
            })

    return json.dumps({"result": "allow", "message": "Port available"})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Command required"}))
        sys.exit(1)
    print(main(" ".join(sys.argv[1:])))
```

### Configuration Example (.claude/settings.json)

```bash
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/check-port.py \"$INPUT\""
          }
        ]
      }
    ]
  }
}
```

## Preventing Dangerous Commands

Dangerous commands such as `rm -rf` or `git push --force` can also be blocked using the PreToolUse hook.

```bash
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$INPUT\" | grep -qE '(rm -rf|git push --force)' && echo 'BLOCK: Dangerous command detected' && exit 1 || exit 0"
          }
        ]
      }
    ]
  }
}
```

-   `rm -rf /home/user/project` → Will be blocked
-   `git push --force origin main` → Will be blocked similarly

## How to Debug Hooks

Here are debugging methods if hooks don't work as intended.

### Enhancing Log Output

You can check the execution results by redirecting the hook script's output to `/tmp/hook-debug.log`.

```bash
python3 /path/to/check-port.py "$INPUT" 2>>&1 | tee -a /tmp/hook-debug.log
```

### Adjusting Timeout

Adjust the hook script's timeout according to your environment. For a process like a port scan, 5 seconds should be sufficient.

## Summary

By leveraging Claude Code's hooks feature, you can automatically prevent port conflicts and the execution of dangerous commands in advance. Simply registering Python scripts or shell commands with the PreToolUse hook significantly enhances the safety of your development workflow. Add these settings to your .claude/settings.json and give it a try!
