---
title: "A Daily Report System to Automatically Aggregate Claude Code + Gemini CLI Usage History Every Morning with Cron"
date: 2026-03-08
topics: ["devtools", "python", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/daily-report-automation"
devto_url: "https://dev.to/soytuber/a-daily-report-system-to-automatically-aggregate-claude-code-gemini-cli-usage-history-every-17hk"
devto_id: 3326331
---

## Why Automate Daily Reports

Manually recording daily AI tool usage is a waste of time. While hook scripts leveraging Claude Code's SessionEnd event at the end of a session exist, they are insufficient for cross-cutting analysis. To visualize token consumption and message frequency on a per-project basis, regular batch processing is essential.

## Data Sources

### Claude Code History Data

Recorded in JSON Lines format on a per-session basis. The data structure per line is as follows:

```bash
{
  "session_id": "sess_abc123",
  "project": "frontend",
  "start_time": "2026-03-01T09:15:00+09:00",
  "messages": [
    {"role": "user", "content": "Reactでサマリー生成"},
    {"role": "assistant", "content": "生成しました"}
  ],
  "token_count": 4210
}
```

### Gemini Temporary Logs

API requests and responses stored in the ~/.gemini/tmp/ directory are processed, targeting only the last 24 hours.

## daily_report.py Design

A design prioritizing memory efficiency has been adopted.

```bash
import json
import os
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

def read_claude_history():
    """セッション履歴をストリーミング読み取り"""
    history_path = os.path.expanduser("~/.claude/projects")
    # プロジェクトディレクトリを走査してJSONLファイルを処理
    for root, dirs, files in os.walk(history_path):
        for f in files:
            if f.endswith(".jsonl"):
                with open(os.path.join(root, f), "r", encoding="utf-8") as fh:
                    for line in fh:
                        if line.strip():
                            yield json.loads(line)

def aggregate_stats(entries):
    """プロジェクト別集計を実施"""
    stats = defaultdict(lambda: {"sessions": 0, "messages": 0, "tokens": 0})
    for entry in entries:
        proj = entry.get("project", "unknown")
        stats[proj]["sessions"] += 1
        stats[proj]["messages"] += len(entry.get("messages", []))
        stats[proj]["tokens"] += entry.get("token_count", 0)
    return stats
```

## Summary Generation with Gemini API

Aggregated data is passed to the Gemini API to generate a summary.

```bash
from google import genai

client = genai.Client()

def generate_summary(stats):
    """Gemini APIでサマリー生成"""
    prompt = f"""
    以下の開発データを要約してください。
    {stats}
    要約は200文字以内で、技術的洞察を含めてください。
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text
```

## SQLite Database Design

Daily report data is stored in an SQLite database.

```bash
CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    session_count INTEGER,
    total_tokens INTEGER,
    project_summary TEXT,
    ai_summary TEXT
);
```

## Weekly Review

A script automatically executed on Fridays analyzes data from the past 7 days. It detects projects with a surge in token consumption.

```bash
SELECT project_summary, SUM(total_tokens) AS total
FROM daily_reports
WHERE date >= date('now', '-7 day')
GROUP BY project_summary
ORDER BY total DESC;
```

## cron Configuration (4 AM JST Daily)

This cron entry executes at 4:00 JST (= 19:00 UTC).

```bash
# /etc/cron.d/daily_report
0 19 * * * user /home/user/daily_report/daily_report.py >> /var/log/daily_report.log 2>&1
```

## Conclusion

This system eliminates manual daily report creation, enabling AI cost optimization per project and early detection of anomalies.
