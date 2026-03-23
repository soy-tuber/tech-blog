---
title: "ローカルRAGツールをNemotron + vLLM + Tool Callingで構築した話"
emoji: "🔍"
type: "tech"
topics: ["LLM", "RAG", "vLLM", "GPU", "Python"]
published: false
canonical_url: "https://media.patentllm.org/blog/ai/soylm-local-rag-nemotron-vllm"
---

## はじめに

単一GPUで完結するローカルファーストのRAGリサーチツールを構築しました。Tool calling + RAGの組み合わせにはかなり試行錯誤が必要でしたので、そのアプローチを共有します。

この記事はReddit r/LocalLLaMAへの投稿を元にしています。

## 技術スタック

- Nemotron Nano 9B v2 Japanese on vLLM（FP16, RTX 5090）
- FastAPI + SQLite FTS5 + Jinja2 — バックエンド全体が1つのapp.pyで完結
- NVIDIAの公式パーサープラグインによるTool CallingとReasoning

![SoyLM RAG Tool - Extract Phase](https://media.patentllm.org/static/soylm-rag-screenshot1.webp)

## 設計上の重要な判断

### Extract → Execute 2段階フロー

質問を投げると、システムはまずLLMを使ってバイリンガルキーワード（EN+JA）を抽出し、ローカルソースに対するFTS5検索とDuckDuckGoウェブ検索を並列実行します。そして見つかったソースをチェックボックス付きで表示。関連するものを選んでExecuteを押すと、そこで初めて生成が始まります。

これにより、100k+トークンのコンテキストを丸ごと投入して「モデルが何とかしてくれ」という方式を回避しています。

### Tool Calling

Nemotron v2はTool Callingに対応していますが、カスタムパーサープラグインが必要です（vLLMの組み込みパーサーはv3用であり、v2には使えません）。`--tool-call-parser nemotron_json` と `--tool-parser-plugin` を指定すると、モデルがウェブ検索のタイミングを自律的に判断します。temp 0.1で驚くほどうまく動きます。

### Prefix Cache ウォームアップ

ソース読み込み時にまとめてキャッシュするのではなく、ユーザーがソースプレビュー（ステップ3）を見ているタイミングでKVキャッシュをウォームアップします。Executeをクリックする頃にはprefixキャッシュが完了済み。vLLMの `--enable-prefix-caching` を使用。

### バイリンガルFTS5検索

ユーザーのクエリ → Nemotronが英語と日本語の両方でキーワード抽出 → OR結合のFTS5 MATCHクエリ。シンプルですが、多言語の特許・研究データに対して効果的です。

![SoyLM RAG Tool - Execute Phase](https://media.patentllm.org/static/soylm-rag-screenshot2.webp)

## パフォーマンス

| 項目 | 数値 |
|---|---|
| 出力速度 | 約80-120 tok/s |
| 最大トークン | 8192 |
| ソース抽出 | 約3-5秒（キーワード抽出 + FTS5 + DDG並列） |
| 完全回答（5ソース + 3ウェブ結果） | 約50秒 |
| GPU | RTX 5090 |

## ソースコード

GitHub: https://github.com/soy-tuber/SoyLM

1ファイルアプリ。`uv pip install -r requirements.txt` で即起動。vLLMとNemotronパーサープラグインは別途必要。

## 元投稿

- Reddit r/LocalLLaMA: https://www.reddit.com/r/LocalLLaMA/comments/1s0lsi8/
- 詳細記事: https://media.patentllm.org/blog/ai/soylm-local-rag-nemotron-vllm
