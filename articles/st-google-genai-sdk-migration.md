---
title: "google-generativeai → google-genai 移行ガイド"
emoji: "🔧"
type: "tech"
topics: ["python", "devtools", "cli", "productivity"]
published: false
canonical_url: "https://media.patentllm.org/blog/dev-tool/google-genai-sdk-migration"
---


## 何が起きたか


google.generativeaiパッケージは非推奨化されました。新しいgoogle-genai SDKへの移行が推奨されています。開発者は早めの移行対応が必要です。


## 新SDK google-genaiの特徴


- Gemini 2.5 Pro/Flashモデルとの統合インターフェース
- コンテキストキャッシュ機能のサポート
- 環境変数GOOGLE_GENAI_API_KEYによる認証の自動読み込み


## 移行の具体手順



### 環境準備


[bash]
pip install --upgrade google-genai
[/bash]


### importの変更


[bash]
# 旧コード（非推奨）
import google.generativeai as genai
genai.configure(api_key="your-key")

# 新コード
from google import genai
client = genai.Client()  # GOOGLE_GENAI_API_KEYを自動読み込み
[/bash]


### generate_contentの書き換え


[bash]
# 旧コード
model = genai.GenerativeModel("gemini-2.5-pro")
response = model.generate_content("Hello")

# 新コード
from google.genai import types

response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="Hello",
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=2048
    )
)
[/bash]


## 既存プロジェクトの移行例


[bash]
# 旧コード（hanrei-db.py）
import google.generativeai as genai
model = genai.GenerativeModel(model_name="gemini-2.5-pro")
response = model.generate_content("この判例を要約してください")

# 新コード（移行後）
from google import genai
from google.genai import types

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="この判例を要約してください",
    config=types.GenerateContentConfig(temperature=0.1)
)
[/bash]


## GenerateContentConfigのパラメータ


- temperature：生成のランダム性を制御します（ファクトチェックには低温度を推奨）
- max_output_tokens：出力の最大トークン数を指定します
- top_k / top_p：サンプリング制御に使用します

注意：旧SDKのGenerationConfigとはクラス名が異なります。frequency_penaltyやpresence_penaltyはgoogle-genai SDKでは直接サポートされていません。


## FutureWarningを放置するとどうなるか


1. 初期段階：FutureWarningが頻発しますが、動作は継続します
2. 中間段階：非推奨モジュールの実行が不安定になる可能性があります
3. 最終段階：サポート終了後は動作不能になるリスクがあります

早めの移行をお勧めします。


## まとめ


- importをfrom google import genaiに変更し、Client()で初期化します
- generate_contentの引数にconfigでGenerateContentConfigを渡します
- 環境変数GOOGLE_GENAI_API_KEYの設定で認証を簡素化できます
- テスト環境で動作確認後、本番環境への移行を進めてください
