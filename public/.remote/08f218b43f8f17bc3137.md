---
title: Claude Codeのトークン消費を削減する — FTS5ナレッジDB + Tier索引設計
tags:
  - Python
  - CLI
  - DevTools
  - productivity
private: false
updated_at: '2026-03-21T21:41:10+09:00'
id: 08f218b43f8f17bc3137
organization_url_name: null
slide: false
ignorePublish: false
---


## 問題


CLAUDE.mdにプロジェクト全体のコーディング規約・テストコマンド・ドキュメントを全て記述すると、毎ターン大量のトークンを消費してしまいます。LLMのコンテキストウィンドウを圧迫し、品質低下を招く可能性があります。


## 解決策：2層構造


「Tier 1索引」と「Tier 2 FTS5 DB」の2層構造で、トークン消費を大幅に削減する設計です。Tier 1は600トークン以内の軽量インデックスで、プロジェクトの基本ルールや頻出コマンドを厳選します。Tier 2はFTS5ベースのフルテキスト検索DBを用意し、必要時のみ深堀り検索を行います。


## 抽出パイプライン


Claude Codeの実行ログから自動抽出するパイプラインを構築しました。コードテンプレートやプロンプトパターンを以下の手順で分類して蓄積します。

[bash]
python3 extract_templates.py --input session_log.jsonl --output templates.json
[/bash]

このスクリプトは、セッションログを解析し、規約・コマンド・テストスクリプトを自動抽出します。FTS5で日本語の全文検索を実施し、重複を除外します。


## ローカルLLMによる分類


Nemotronをローカルで動作させ、thinking OFF + max_tokens 64の設定で高速分類を実施します。抽出されたテンプレートを高速で「必須」「任意」「非該当」に分類します。

[bash]
response = nemotron_classify(
    input_text=template,
    max_tokens=64,
    thinking=False
)
[/bash]


## Gemini大コンテキストでのTier 1選別


分類されたテンプレートを、Geminiの大コンテキストで優先度順に絞り込みます。選定基準は「実行頻度（過去7日間）」「プロジェクト重要度」の2軸で評価します。

[bash]
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"以下のテンプレート一覧から重要度順にTier1を選別してください:\n{tier_list}"
)
[/bash]

上位テンプレートはtier_1_index.jsonに保存され、毎ターンのプロンプト生成時に優先的に参照されます。


## memory.dbによるセッション横断記憶


FTS5を活用したメモリDB（memory.db）で、複数セッションの知識を統合管理します。

[bash]
SELECT * FROM rules WHERE rules MATCH 'テストコマンド';
[/bash]


## 効果


- 毎ターンのトークン消費を大幅に削減
- 必要な情報のみを効率的に検索・提供
- Nemotronのローカル推論とGeminiの大コンテキストを組み合わせた選別パイプライン


## まとめ


Tier 1索引で基本ルールを効率管理し、FTS5で必要時のみ深堀り検索するアーキテクチャは、LLMのコンテキストウィンドウ制約を克服する鍵となります。Nemotronのローカル推論とGeminiの大コンテキストを組み合わせた「選別→検索」のパイプラインは、個人開発環境で即実装可能です。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/dev-tool/claude-code-knowledge)*
