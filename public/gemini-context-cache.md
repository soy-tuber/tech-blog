---
title: Gemini Context Cachingで大規模ドキュメント分析のAPI費用を削減する
tags:
  - Python
  - MachineLearning
  - AI
  - LLM
private: false
updated_at: '2026-03-21T21:41:10+09:00'
id: d8792c225f58392b5727
organization_url_name: null
slide: false
ignorePublish: false
---


## Context Cachingとは


Google GeminiのContext Cachingは、一度入力したコンテキストをキャッシュし、後続のリクエストで再利用する機能です。キャッシュ済みトークンは通常料金の約25%で利用できるため、大幅なコスト削減が可能です。


### 基本仕様


- キャッシュ有効期間：デフォルト3,600秒（1時間）
- トークン要件：最小32,768トークン
- モデルごとの分離：キャッシュはモデル名と連動して管理されます


## 使いどころ



### 大規模DB分析


FTS5+BM25で構築したSQLite DBを分析対象とする場合、Context Cachingを活用することで効果的です。

- キーワード抽出フェーズ：Flashモデルで高速処理
- 回答生成フェーズ：Proモデルで高精度分析
- ファクトチェックフェーズ：教師データをキャッシュ化し、処理時間を短縮


### バッチ分析


バッチ処理時は同一コンテキストを全サンプルで再利用することが効果的です。

[bash]
from google import genai
from google.genai import caching

client = genai.Client()

# キャッシュ作成（32,768トークン以上が必要）
cached_content = caching.CachedContent.create(
    client=client,
    name="patent_batch_cache",
    contents=[{"text": doc["title"]} for doc in patent_docs[:1000]],
    model="gemini-2.5-flash",
    config={"expire_time": "2026-03-09T00:00:00Z"}
)

# キャッシュを使った生成
for doc in patent_docs:
    result = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=doc["text"],
        cached_content=cached_content.name
    )
[/bash]


## コスト計算例


75,458トークンの教師データの場合：
- キャッシュなし：通常料金
- キャッシュあり：通常料金の約25%

バッチ処理で同じコンテキストを繰り返し使う場合、キャッシュの効果は非常に大きくなります。


## 制限事項と注意点


- キャッシュ作成時は32,768トークン以上が必要です
- モデルごとにキャッシュが分離されるため、異なるモデル間でのキャッシュ共有はできません
- 有効期限を分析処理時間に合わせて設定することが重要です


## まとめ


Context Cachingを適切に活用することで、大規模データ分析のAPIコストを大幅に削減し、処理時間を短縮できます。キーワード抽出にFlashモデル、回答生成にProモデルを使い分け、バッチ処理時は同一コンテキストを再利用することが成功の鍵です。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/ai/gemini-context-cache)*
