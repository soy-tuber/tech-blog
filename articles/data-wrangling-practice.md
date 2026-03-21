---
title: "SQLite・JSONL・XML・TSVの使い分け — PatentLLMのデータ整理術"
emoji: "🔧"
type: "tech"
topics: ["python", "devtools", "cli", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/blog/dev-tool/data-wrangling-practice"
---


## はじめに


PatentLLM（特許検索AI）とHanrei-DB（判例検索AI）は、どちらもPython + Streamlit + SQLiteで構築した個人プロジェクトです。開発を通じて、データ形式の選択がアプリの保守性と開発速度に直結することを実感しました。本記事では、実際に使い分けたデータ形式ごとの判断基準と実装上のノウハウを整理します。


## SQLite3：アプリのバックエンド


PatentLLMとHanrei-DBの両方で、検索対象データの格納にSQLite3を採用しました。

選定理由：
- サーバープロセス不要。.dbファイル1つで完結
- FTS5（全文検索）が組み込みで使える
- Pythonのsqlite3モジュールが標準ライブラリ
- Streamlitとの相性が良い（読み取り中心の用途）

Hanrei-DBでは判例テキストをFTS5でインデックス化し、キーワード検索とGemini 3.1 ProによるAI要約を組み合わせています。

[bash]
import sqlite3

conn = sqlite3.connect("hanrei.db")
conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS cases USING fts5(title, content)")

# 検索
results = conn.execute(
    "SELECT title, snippet(cases, 1, '<b>', '</b>', '...', 30) FROM cases WHERE cases MATCH ?",
    ("損害賠償 AND 契約解除",)
).fetchall()
[/bash]

注意点：
- 同時書き込みに弱い（WALモードでもシングルライター）
- Streamlitはリクエストごとにスクリプトが再実行されるため、コネクションはキャッシュするかリクエストスコープで管理する
- 数十万件までは問題なし。それ以上はインデックス設計が重要


## JSONL：LLMとのデータ受け渡し


Gemini APIやローカルLLMとのやりとりでは、JSONLが最も扱いやすいです。

[bash]
{"id": "H25-01234", "title": "損害賠償請求事件", "summary": "...", "label": "民事"}
{"id": "H26-05678", "title": "特許権侵害差止請求事件", "summary": "...", "label": "知財"}
[/bash]

メリット：
- 1行1レコードでストリーム処理が可能（メモリに全量載せる必要がない）
- 追記が容易（ファイル末尾にappendするだけ）
- 1行が壊れても他の行に影響しない
- jqコマンドで即座に中身を確認できる

[bash]
# 件数確認
wc -l cases.jsonl

# 先頭3件を整形表示
head -3 cases.jsonl | jq .

# 特定ラベルだけ抽出
cat cases.jsonl | jq -r 'select(.label == "知財") | .title'
[/bash]

PatentLLMでは、特許庁のCSVデータをJSONLに変換してからSQLiteに投入するパイプラインを組みました。CSV→JSONL→SQLiteの流れにすることで、中間データの検証が容易になります。


## XML：ブログ記事管理


このブログ（Local AI Dev Log）自体が、記事データをXMLで管理しています。FastAPIがリクエスト時にXMLを読み、Jinja2テンプレートでレンダリングする構成です。

[bash]
<articles>
  <item>
    <id>data-wrangling-practice</id>
    <category>data</category>
    <title>SQLite・JSONL・XML・TSVを使い分けるデータ整理術</title>
    <price>0</price>
    <summary>...</summary>
    <content>...</content>
  </item>
</articles>
[/bash]

XMLを選んだ理由：
- 記事数が数十件程度で、DBを使うほどではない
- ElementTreeが標準ライブラリにあり外部依存がゼロ
- カテゴリやタグの階層構造を自然に表現できる
- 手動編集も可能（人間が読める）

[bash]
import xml.etree.ElementTree as ET

tree = ET.parse("data/articles_merged.xml")
root = tree.getroot()
for item in root.findall("item"):
    if item.find("category").text == "llm":
        print(item.find("title").text)
[/bash]

数百件を超えるならSQLiteに移行すべきですが、30〜50件程度のブログ記事管理にはXMLで十分です。


## TSV/CSV：外部データの取り込み


官公庁データ、金融データAPI、スクレイピング結果など、外部から取得するデータはCSVまたはTSVで来ることが多いです。

PatentLLMでは特許庁の公開データ（CSV）を取り込んでいます。

[bash]
import csv
import sqlite3
import json

conn = sqlite3.connect("patent.db")
conn.execute("CREATE TABLE IF NOT EXISTS patents (id TEXT PRIMARY KEY, title TEXT, abstract TEXT, date TEXT)")

with open("patents.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        conn.execute(
            "INSERT OR IGNORE INTO patents VALUES (?, ?, ?, ?)",
            (row["出願番号"], row["発明の名称"], row["要約"], row["出願日"])
        )
conn.commit()
[/bash]

CSVの罠：
- エンコーディング問題（Shift_JIS、BOM付きUTF-8）
- フィールド内の改行・カンマ（クォート処理の不備）
- 型情報がない（数値と文字列の区別は読み込み側の責任）

対策として、取り込み時にJSONLへ変換する中間ステップを挟むと、データ検証がしやすくなります。

[bash]
# CSV → JSONL変換
import csv, json

with open("patents.csv", encoding="utf-8") as f_in, open("patents.jsonl", "w", encoding="utf-8") as f_out:
    for row in csv.DictReader(f_in):
        f_out.write(json.dumps(row, ensure_ascii=False) + "\n")
[/bash]


## 使い分けまとめ


- アプリのバックエンド（検索・永続化）→ SQLite3
- LLMとのデータ受け渡し・学習データ → JSONL
- 少数の構造化コンテンツ管理 → XML
- 外部データの取り込み入口 → CSV/TSV（経由地として）

共通する原則：catやjqで中身を確認できるテキストベースの形式を選びます。バイナリ形式（Parquet、Protocol Buffers等）は、数百万件以上のデータや型安全性が必須な場面まで出番を待てばよいです。
