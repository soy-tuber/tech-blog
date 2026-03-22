---
title: DuckDuckGo検索 + ローカルLLMで作る無料リサーチエージェント
tags:
  - Python
  - MachineLearning
  - AI
  - LLM
private: false
updated_at: '2026-03-21T21:41:10+09:00'
id: ff94970395aeca717dc5
organization_url_name: null
slide: false
ignorePublish: false
---


## なぜDuckDuckGo + ローカルLLMか


調査を行う際、有料API（Brave Search等）を利用するケースが主流ですが、ddgsライブラリを活用すれば、APIキー不要でWeb検索が可能です。

- コスト面：完全無料で利用できます（ただしrate limitあり）
- ローカルLLM連携：検索結果をNemotron（vLLM実行）に渡し、RAGで高精度な分析を実現します

なお、ddgsはDuckDuckGoの非公式ライブラリであり、検索クエリ自体はDuckDuckGoのサーバーに送信されます。完全なデータローカル処理ではない点にご注意ください。


## ddgsライブラリの使い方


[bash]
pip install duckduckgo-search
[/bash]

[bash]
from duckduckgo_search import DDGS

ddgs = DDGS()
results = ddgs.text("2026年 技術トレンド", region="jp-jp", max_results=5)
for result in results:
    print(f"Title: {result['title']}, URL: {result['href']}")
[/bash]

- リージョン指定：region="jp-jp"で日本語検索結果を優先します
- ニュース検索：ddgs.news("AI規制", region="jp-jp")でニュースフィードを取得できます
- DuckDuckGoは公式にはスクレイピングを推奨していないため、過度なリクエストはブロックされる可能性があります


## 検索結果をNemotronに注入するRAGパイプライン


[bash]
from duckduckgo_search import DDGS
from openai import OpenAI

# 1. ddgsで検索結果を取得
ddgs = DDGS()
search_results = ddgs.text("最新GPUベンチマーク", region="jp-jp", max_results=3)
context = "\n".join([f"【{r['title']}】{r['body']}" for r in search_results])

# 2. vLLMのOpenAI互換APIで要約
client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
response = client.chat.completions.create(
    model="nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
    messages=[
        {"role": "system", "content": "以下の検索結果を参考に回答してください"},
        {"role": "user", "content": f"{context}\n\n上記情報をもとに、最新技術トレンドを300字で要約してください。"}
    ]
)
print(response.choices[0].message.content)
[/bash]


## Brave Search APIとの比較


- ddgs（無料）：APIキー不要、日本語検索に強い、個人開発・プロトタイプ向け
- Brave Search API（有料）：公式API、高スループット、企業向け大規模分析向け


## バッチ記事生成への応用


ddgs + Nemotronの組み合わせで、検索結果をもとにしたコンテンツ自動生成も可能です。検索→要約→Markdown出力の流れで、出典URLを明記したトレーサビリティのある記事を生成できます。


## まとめ


DuckDuckGo検索 + ローカルLLMの組み合わせは、無料で実現可能なRAGパイプラインです。検索データのローカル処理によるプライバシー保護（検索クエリ送信を除く）と低コストな調査自動化を実現します。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/ai/ddg-nemotron-research)*
