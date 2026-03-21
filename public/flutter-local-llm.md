---
title: ローカルLLMとFlutterで5-in-1アプリを作る
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


## はじめに


「クラウドにデータを送らずにAIを活用したい」。ローカルLLMの最大の強みは、手元のデータを外部に出さずに処理できることです。

Desktop PC（RTX 5090）でvLLMを使ってNemotronを動かし、Flutter Webで5つの機能を1つのアプリに統合しました。


## 開発方針の転換


▼最初のアイデア：汎用AIツール

当初は秘密日記AI、パスワード強度チェッカーなど汎用的なツールを5つ作る予定でした。しかし「ローカルLLMならでは」の価値が薄い。

▼転換：自分の開発データを活用する

手元にあるClaude Codeのセッション履歴データに注目。自分の開発履歴をLLMに分析させるというコンセプトに切り替えました。


## 5つの機能


1. Claude Code→ブログ記事：セッション履歴から技術記事を自動生成
2. プロジェクト振り返りAI：全セッションを横断分析してレトロスペクティブ
3. ローカルファイルQ&A：機密ファイルに対して安全に質問
4. コード→クイズ生成：ソースコードから理解度テストを生成
5. Git→開発ストーリー：コミット履歴を物語形式に変換


## 技術構成


▼アーキテクチャ

- Desktop PC（RTX 5090）：vLLMでNemotronを起動。OpenAI互換APIを提供
- Flask APIサーバー：データの前処理とLLM呼び出しを担当
- Flutter Webフロントエンド：5機能をタブ切り替えで統合

Chromebookは常時稼働サーバーとして各サービスを提供し、Desktop PCはGPU推論専用。Tailscale VPN経由で内部接続しています。

▼Flask + Flutter連携

[bash]
# Flaskサーバー（app.py）
from flask import Flask, jsonify, request
import requests

app = Flask(__name__, static_folder='flutter_build/web')

VLLM_URL = 'http://<TAILSCALE_IP>:8000/v1/chat/completions'

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    # vLLMのOpenAI互換APIにリクエスト（Tailscale経由）
    response = requests.post(VLLM_URL, json={
        'model': 'nvidia/Nemotron-Mini-4B-Instruct',
        'messages': [{'role': 'user', 'content': data['prompt']}]
    })
    return jsonify(response.json())
[/bash]

▼Flutter Webのビルドと配信

[bash]
# Flutter Webビルド
cd flutter_app
flutter build web

# ビルド成果物をFlaskの静的ファイルディレクトリにコピー
cp -r build/web ../flutter_build/web
[/bash]

FlaskがFlutter Webのビルド済みファイルを配信するため、1つのサーバーで全てが動作します。


## ポイント：ローカルLLMの実用性


- クラウドAPIと違い、データが外部に一切出ない
- vLLMのOpenAI互換APIにより、コード変更なしでモデルを切り替え可能
- FlutterのレスポンシブUIで、PCでもスマホでも利用可能


## まとめ


ローカルLLMとFlutterの組み合わせは「データを外に出さない」という制約下でAIアプリを構築する実用的な選択肢です。Flask + Flutter Webの連携により、バックエンドとフロントエンドを1サーバーで完結させられます。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/ai/flutter-local-llm)*
