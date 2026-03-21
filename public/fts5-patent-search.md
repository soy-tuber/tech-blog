---
title: FTS5で354万件の特許データを高速検索する
tags:
  - ai
  - machinelearning
  - llm
  - python
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---


## はじめに：LIKE検索の限界


PatentLLMの特許データベース（354万件）で「バッテリー」を検索すると、結果がなかなか表示されない。`LIKE '%battery%'`による全件スキャンは、実用的な速度ではありませんでした。

LIKE検索の問題は3つ：
- 全テーブルスキャンによるパフォーマンス劣化
- 語尾の揺れ（battery / batteries）に非対応
- 「バッテリー OR リチウム NOT ナトリウム」のような複合検索が困難


## FTS5とは


SQLiteに組み込まれた全文検索エンジンです。転置インデックスを事前に構築し、キーワードから該当行を即座に引きます。

主なメリット：
- 転置インデックスによる高速検索
- BM25ランキング：検索語との関連度で自動スコアリング
- 複合検索のネイティブ対応：`battery OR lithium NOT sodium` が1行で書ける


## 実装手順


▼FTS5テーブルの構築

[bash]
-- FTS5仮想テーブルを作成
CREATE VIRTUAL TABLE cases_fts USING fts5(
    raw_case_name,
    summary,
    analysis_json
);

-- 既存データを投入
INSERT INTO cases_fts SELECT raw_case_name, summary, analysis_json FROM merged_cases;
[/bash]

▼検索クエリの比較

[bash]
-- 旧：LIKE検索（全件スキャン・ランキングなし）
SELECT * FROM merged_cases
WHERE raw_case_name LIKE '%battery%'
   OR summary LIKE '%battery%';

-- 新：FTS5検索（インデックス利用・BM25ランキング付き）
SELECT *, rank FROM cases_fts
WHERE cases_fts MATCH 'battery'
ORDER BY rank;
[/bash]

FTS5では全件スキャンが不要になり、354万件でも検索が即座に返ります。


## MCP連携時のクエリチューニング


Claude CodeからMCPサーバー経由でPatentLLMのDBに接続し、特許分析を行う際に「全仮説でDBヒット0件」という問題に直面しました。

▼原因：キーワード設計の不整合

Gemini APIが生成するキーワードがAND連結の長いフレーズになり、実際のデータとマッチしないケースが発生。

[bash]
-- 問題例：広すぎるクエリ（汎用語で大量ヒット）
SELECT COUNT(*) FROM cases_fts WHERE cases_fts MATCH 'patent';

-- 問題例：厳しすぎるクエリ（AND連結で0件）
SELECT COUNT(*) FROM cases_fts
WHERE cases_fts MATCH 'retrieval AND augmented AND generation AND pipeline';
[/bash]

▼解決：手動キーワード優先ロジック

[bash]
# Geminiに全て委任する代わりに、手動キーワードを優先
if 'fts_keywords' in hypotheses[hypothesis]:
    query = hypotheses[hypothesis]['fts_keywords']
else:
    query = analyze_query(hypothesis)
[/bash]

▼キーワード設計の3段階プロセス

1. 汎用キーワードでヒット数を計測（COUNT(*)で確認）
2. FTS5の複合検索構文で絞り込み（OR / AND / NOT を組み合わせ）
3. 目標件数（10〜30件）に収まるよう微調整


## まとめ


- FTS5は既存のSQLiteデータで即座に導入可能
- 354万件でもミリ秒単位の検索を実現
- MCP連携時はキーワードの粒度に注意。自動生成クエリは必ず実データで検証する

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/ai/fts5-patent-search)*
