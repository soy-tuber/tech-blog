---
title: Claude Code + Gemini CLIの使用履歴をcronで毎朝自動集計する日報システム
tags:
  - Python
  - CLI
  - DevTools
  - productivity
private: false
updated_at: '2026-03-21T21:41:11+09:00'
id: 07fba78b68e2311c617c
organization_url_name: null
slide: false
ignorePublish: false
---


## なぜ日報を自動化するか


毎日のAIツール使用状況を手動で記録する作業は時間の無駄です。Claude Codeのセッション終了時のSessionEndイベントを活用するhookスクリプトも存在しますが、横断的な分析には不十分です。プロジェクト単位のトークン消費量やメッセージ頻度を可視化するためには、定期的な一括処理が不可欠です。


## データソース



### Claude Codeの履歴データ


セッション単位でJSON Lines形式で記録されます。1行あたりのデータ構造は以下の通りです。

[bash]
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
[/bash]


### Geminiの一時ログ


~/.gemini/tmp/ ディレクトリに保存されるAPIリクエスト・レスポンスを、直近24時間分のみ処理対象としています。


## daily_report.pyの設計


メモリ効率を考慮した設計を採用しました。

[bash]
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
[/bash]


## Gemini APIによるサマリー生成


集計データをGemini APIに渡してサマリーを生成します。

[bash]
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
[/bash]


## SQLiteデータベース設計


日報データはSQLiteデータベースに蓄積します。

[bash]
CREATE TABLE IF NOT EXISTS daily_reports (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    session_count INTEGER,
    total_tokens INTEGER,
    project_summary TEXT,
    ai_summary TEXT
);
[/bash]


## 週次振り返り


金曜日に自動実行されるスクリプトで、直近7日分のデータを分析します。トークン消費量の急増プロジェクトを検出します。

[bash]
SELECT project_summary, SUM(total_tokens) AS total
FROM daily_reports
WHERE date >= date('now', '-7 day')
GROUP BY project_summary
ORDER BY total DESC;
[/bash]


## cron設定（毎朝4時JST）


JST 4:00（= UTC 19:00）に実行するcronエントリです。

[bash]
# /etc/cron.d/daily_report
0 19 * * * user /home/user/daily_report/daily_report.py >> /var/log/daily_report.log 2>&1
[/bash]


## まとめ


本システムにより、手作業による日報作成を廃止し、プロジェクト単位のAIコスト最適化と異常値の早期発見が可能になります。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/dev-tool/daily-report-automation)*
