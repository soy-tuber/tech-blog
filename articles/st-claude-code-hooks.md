---
title: "Claude Codeのhooks機能でポート衝突・危険コマンドを事前に自動防止する"
emoji: "🔧"
type: "tech"
topics: ["python", "devtools", "cli", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/blog/dev-tool/claude-code-hooks"
---


## Claude Code hooksとは


Claude Codeのhooks機能は、ツール実行前後のイベント駆動型自動化を可能にします。PreToolUse（実行前検証）、PostToolUse（実行後処理）、UserPromptSubmit（プロンプト送信時）など複数のライフサイクルイベントに対応しており、事前にルールを強制することで開発の安全性を向上させます。特にPreToolUseフックは、実行前の検証やブロック処理に適しています。


## PreToolUse hookの仕組み


PreToolUseフックは、ツール実行前に自動的に検証ロジックを実行します。.claude/settings.jsonに登録したスクリプトが、コマンド実行前に検証を行います。

実行フローは以下の通りです。

1. ユーザーがpython app.py --port 8000と入力
2. Claude CodeがPreToolUseフックを起動
3. 登録スクリプトがコマンド内容を解析し、ポート8000が使用中か判定
4. 使用中の場合、コマンド実行をブロック


## ポート衝突防止スクリプトの実装


[bash]
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
[/bash]


### 設定例（.claude/settings.json）


[bash]
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
[/bash]


## 危険コマンド防止


rm -rfやgit push --force等の危険なコマンドも、PreToolUseフックでブロックできます。

[bash]
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
[/bash]

- rm -rf /home/user/project → ブロックされます
- git push --force origin main → 同様にブロックされます


## hookのデバッグ方法


フックが意図通りに動かない場合のデバッグ手法です。


### ログ出力の強化


フックスクリプトの出力を/tmp/hook-debug.logにリダイレクトすることで、実行結果を確認できます。

[bash]
python3 /path/to/check-port.py "$INPUT" 2>>&1 | tee -a /tmp/hook-debug.log
[/bash]


### タイムアウトの調整


フックスクリプトのタイムアウトは環境に応じて調整してください。ポートスキャン程度の処理であれば、5秒あれば十分です。


## まとめ


Claude Codeのhooks機能を活用することで、ポート衝突や危険コマンドの実行を事前に自動防止できます。PreToolUseフックにPythonスクリプトやシェルコマンドを登録するだけで、開発フローの安全性が大幅に向上します。.claude/settings.jsonに設定を追加して、ぜひ活用してみてください。
