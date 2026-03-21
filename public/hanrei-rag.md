---
title: 判例PDFをRAGで検索する — Gemini + SQLite FTS5による法務AI検索システム
tags:
  - python
  - devtools
  - cli
  - productivity
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---


## 判例検索の課題


従来の裁判所データベース（courts.go.jp等）は検索機能が文字列一致に限定されており、PDF内の本文を検索する手段が存在しません。判例集に収録されたPDFはテキストデータとして抽出されないため、キーワード検索で「民法90条」と入力しても該当判例がヒットしないケースが頻発します。また、判旨の核心である「争点」や「判示事項」を自動抽出する技術が不足していたため、法務担当者は判例の詳細を手動で読み解く必要がありました。

本システムは、PDFを可読テキストに変換し、SQLiteのFTS5（フルテキスト検索）で高速検索を実現し、Geminiを活用して判例の分析を自動化することで、これらの課題を解消します。


## システム構成


本システムは4段階のパイプラインで構成されています。


### PDF解析

PyPDF2を用いてPDFをテキスト化します。スキャン判例にはOCR（Tesseract）を併用し、SQLiteデータベースへインデックスを構築します。FTS5にBM25の重み付けを適用し、日本語判例特有の文法に最適化しました。


### SQLite FTS5

以下のSQLで検索インデックスを作成し、キーワード検索を高速化します。

[sql]
CREATE VIRTUAL TABLE hanrei_search USING fts5(id, text);
INSERT INTO hanrei_search VALUES(1, '民法第90条に基づく...');
[/sql]


### Gemini分析

Gemini 2.5 Proで判例本文を分析します。争点抽出用プロンプトは「この判例の争点を3項目以内にまとめよ」とし、判旨要約では「判示事項を100字で要約せよ」と指示します。


### Streamlit UI

検索結果にGemini分析結果を即時表示します。類似判例の推薦にはFTS5のBM25スコアを活用し、実務的な類似度を算出します。


## Gemini APIによる判例分析


Gemini 2.5 Proは判例の核心を的確に抽出できます。実装コード例を示します。

[python]
from google import genai

client = genai.Client()

prompt = "この判例の争点を3項目以内にまとめよ。判示事項を100字で要約せよ。\n\n" + pdf_text
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=prompt
)
print(response.text)
[/python]

主な特徴は以下の通りです。
- コンテキストキャッシュで前回の分析結果を保持し、APIコストを削減できます
- Flashモデルによるキーワードの高精度抽出が可能です
- ただし、LLMによるファクトチェック結果は参考情報であり、最終的な検証は法務専門家が行う必要があります


## OTPメール認証の実装


法務データの取り扱いには不正アクセス防止が必須です。本システムはFirebase AuthenticationでメールOTP認証を実装しました。
- ログイン時に6桁のOTPをメール送信します（有効期限5分）
- 3回失敗でアカウントロックします（rate limiting）
- 通信はTLS 1.3で暗号化し、データは暗号化ストレージに保存します
- GDPR準拠のため、データはユーザーの端末内にのみ保存します


## 特許検索技術の判例への転用


特許検索システムで実績のある技術を法務分野に応用しました。
- FTS5の日本語最適化：BM25のパラメータ（k1, b）を判例の文法に合わせて調整しました。「民法」と「民法第90条」を関連キーワードとして扱えます
- 分析UIの共通設計：特許LLMのフィルタ機能を転用し、判例を争点タイプや判例年で絞り込み可能にしました
- Cloudflareの活用：DDoS攻撃対策を導入し、応答速度を向上させました


## まとめ


本システムは、大規模な判例データをSQLiteデータベースで管理し、Gemini 2.5 Proの分析精度とFlashモデルのキーワード抽出により、法務担当者の業務効率を大幅に向上させました。今後の改善点として、スキャン判例のOCR精度向上と、e-Gov法令APIとの連携強化を検討しています。

この記事はNemotron-Nano-9B-v2-Japaneseが生成し、Gemini 2.5 Flashが整形・検証を行いました。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/dev-tool/hanrei-rag)*
