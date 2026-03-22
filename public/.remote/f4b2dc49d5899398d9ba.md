---
title: Global MCPにsqliteサーバーを追加したものの、PatentLLM分析で0件ヒット！FTS5のキーワード調整とGemini分析の連携で解決
tags:
  - Python
  - MachineLearning
  - AI
  - LLM
private: false
updated_at: '2026-03-21T21:41:11+09:00'
id: f4b2dc49d5899398d9ba
organization_url_name: null
slide: false
ignorePublish: false
---

## 導入：Global MCPとsqliteサーバーの設定から始まった課題

グローバルMCPにsqliteサーバーを追加し、PatentLLMの特許分析を実行しようとしたところ、全仮説で**DBヒット0件**という予期せぬ結果に直面しました。設定内容は以下の通りです：

- **サーバー名**: sqlite
- **コマンド**: `npx -y mcp-server-sqlite-npx`
- **DBパス**: `/home/soy/Projects/PatentLLM/data/merged_patents.db`

DBスキーマ確認では、`merged_cases`テーブルに350万件超の英語特許データが存在し、FTS5による全文検索が可能な状態でした。しかし、Gemini 3.1 Pro APIが生成するキーワードが**AND連結の長いフレーズ**（例: `"retrieval AND augmented AND generation"`）となり、実際の特許データとマッチしない状況が発生。特に汎用キーワード（`patent`, `model`）が多すぎることで、逆に**10-30件の目標ヒット数を大幅に超過**するケースもありました。

## 問題の本質：FTS5クエリの設計とGeminiの分析フローの不整合

### 問題1：キーワードが「広すぎる」か「厳しすぎる」
- 初期キーワード例: `"RAG pipeline"` → **164万件ヒット**（目標10-30件の46倍）
- 対策としてFTS5の括弧構文を調整（例: `"retrieval augmented generation"`）で**51件**まで絞れたが、スクリプト実行では依然0件

### 問題2：Geminiが[Inference]タグの架空データを生成
- DBヒット0件を受けてGeminiが独自に特許番号を生成し、`[Inference]`タグ付きの分析結果を返す
- 実際のDBデータを活用した分析が行われていない

## 解決までのストーリー：手動FTSキーワードの導入とスクリプト修正

### ステップ1：DBヒット数の精密計測
`SELECT COUNT(*)`で仮説ごとのヒット数を計測し、以下の傾向を発見：
```markdown
| 仮説 | 初期ヒット数 | 修正後ヒット数 |
|------|--------------|----------------|
| h1   | 1,642,248    | 51             |
| h2   | 553,621      | 12             |
| h3   | 520,202      | 23             |
| h5   | 1,367,727    | 39             |
```
→ 汎用キーワードが`AND`で連結されると急激にヒット数が増加する現象を確認

### ステップ2：Gemini分析フローとの連携設計
スクリプト`run_prior_art_search.py`の`run_search()`関数を修正。重要な変更点は：
```python
# 修正前（Geminiに全てのキーワード生成を委任）
query = analyze_query(hypothesis)  # GeminiがAND連結の厳しすぎるクエリを生成

# 修正後（手動キーワード優先ロジックを追加）
if 'fts_keywords' in hypotheses[hypothesis]:
    query = hypotheses[hypothesis]['fts_keywords']  # 手動設定を優先
else:
    query = analyze_query(hypothesis)  # Geminiの分析は常に実行
```

### ステップ3：実際の分析で確認した課題
- 手動キーワードを設定しても**DBヒット0件**が継続
- 原因を調査したところ、`FTS5のクエリ構文エラー`（例: 正規表現の不備）が判明
- 具体的な修正例: 
  ```diff
  - "patent portfolio" AND (comparison OR similarity)
  + "patent portfolio" AND (comparison|similarity)  # FTS5では|でORを表現
  ```

## 結論：実務で活用できる3つのベストプラクティス

### 1. **FTS5クエリの「|」でORを明示的に記述**
```diff
+ "patent portfolio" AND (comparison|similarity)  # 修正ポイント
- "patent portfolio" AND (comparison OR similarity)
```
`OR`キーワード単体ではFTS5がANDと解釈するため、`|`記号を使用する必須設計

### 2. **Gemini分析とDB検索の役割分担**
- **Gemini**: クエリ分析・レポート生成（`[Inference]`タグ付きの価値ある分析を提供）
- **DB検索**: 手動で設計したFTSキーワードで**実データをフィルタリング**
→ 両者を並行実行することで、分析の信頼性と実用性を両立

### 3. **キーワード設計の「3段階フィルタリング」**
```mermaid
graph LR
A[汎用キーワード] --> B(AND連結でヒット数爆増)
B --> C[FTS5で|を使った厳密なOR]
C --> D[実際のDBヒット数を計測]
D --> E[10-30件に収まるよう微調整]
```
汎用キーワード→厳密な構文→実測値で調整するプロセスが必須

## おわりに：現場で活きる技術選定のポイント

この事例から、**全文検索システムの設計では「スキーマ理解」と「実データ検証」が不可欠**であることがわかりました。特にMCP連携時は：
- SQLiteサーバーのDBスキーマを事前に確認
- FTS5クエリは実機でヒット数を計測しながら調整
- Geminiの分析結果を過信せず、DBデータの実在性を必ず確認

技術ブログの参考になれば幸いです。今後も実データに基づく分析を実現するために、継続的な改善を楽しみにしています！

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/ai/nemotron-fts5-gemini-pipeline)*
