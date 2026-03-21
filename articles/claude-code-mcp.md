---
title: "Claude CodeのMCPサーバー活用術"
emoji: "🔧"
type: "tech"
topics: ["python", "devtools", "cli", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/blog/dev-tool/claude-code-mcp"
---


## はじめに：DB操作のコンテキスト切り替え問題


SQLiteは軽量で依存が少ない優れたデータベースですが、開発中にターミナルでクエリを実行し、エディタに戻り、また別のDBファイルを開いて…という作業のコンテキスト切り替えが非効率でした。

Claude CodeのMCP（Model Context Protocol）サーバー機能を使えば、この問題を解決できます。


## MCPサーバーとは


MCPは、Claude Codeに外部ツールを接続するためのプロトコルです。MCPサーバーを登録すると、Claude Codeが直接そのツールを呼び出せるようになります。


## SQLite MCPサーバーの導入


▼セットアップ（1コマンド）

[bash]
# uvx経由でMCPサーバーを登録
claude mcp add sqlite -- uvx mcp-server-sqlite --db-path ~/Projects/PatentLLM/data/merged_patents.db
[/bash]

uvxはuvに同梱されているツールランナーで、Pythonパッケージをグローバルにインストールせずに直接実行できます。uv環境であれば追加セットアップは不要です。

▼導入の決め手

- uvx経由で軽量実行：グローバルインストール不要
- Anthropic公式提供による安定性
- 豊富なツールセット：テーブル一覧、スキーマ取得、読み取り・書き込みクエリ


## 実際の開発ワークフロー


MCPサーバーを登録すると、Claude Codeとの会話の中で自然にDB操作ができます。

[bash]
# 例：Claude Codeに自然言語で依頼するだけ

「merged_patents.dbのテーブル一覧を見せて」
→ Claude Codeがlist_tablesツールを自動で呼び出す

「merged_casesテーブルのスキーマを確認して」
→ describe_tableツールでカラム定義を取得

「status = 'active' のレコードを10件取得して」
→ read_queryツールでSELECT文を自動生成・実行
[/bash]

ポイントは、SQLを自分で書く必要がないことです。自然言語で依頼すれば、Claude Codeが適切なクエリを生成・実行します。


## PatentLLMでの活用例


PatentLLMの`merged_patents.db`（354万件）を接続し、以下のような作業がClaude Code内で完結するようになりました：

- テーブル構造の即時把握（新規参加メンバーのオンボーディング）
- FTS5検索のクエリテスト（MATCH句の動作確認）
- データ品質チェック（NULL率、重複レコードの確認）


## 複数DB環境の切り替え


[bash]
# DB接続先を変更する場合
claude mcp remove sqlite
claude mcp add sqlite -- uvx mcp-server-sqlite --db-path ~/Projects/hanrei-db/hanrei.db
[/bash]

プロジェクトごとにDB接続先を切り替えれば、開発環境ごとのデータ操作も効率化できます。


## まとめ


- MCPサーバーでSQLite操作をClaude Code内に統合
- 自然言語でDB操作が可能。SQL手書きの手間が減る
- uvx経由の1コマンドで導入完了
