---
title: "Nemotron 9BをvLLMで動かしOpenAI互換APIで使う実践ガイド"
emoji: "🔧"
type: "tech"
topics: ["gpu", "nvidia", "deeplearning", "vllm"]
published: false
canonical_url: "https://media.patentllm.org/blog/gpu-inference/nemotron-vllm-guide"
---


## はじめに


最近Qiitaで「Nemotron-Nano-9B-v2-Japaneseをllama.cppで動かす記事」が話題になりました。その記事ではOllamaのゼロ除算バグ対策としてllama.cppの手動ビルドとGGUF変換が必須でしたが、本記事ではよりシンプルかつ実用的なアプローチとして「vLLM + OpenAI互換API」を紹介します。vLLMを使えばGGUF変換不要・Ollamaのトラブル回避・既存コードのそのまま流用が可能で、3行のコマンドでサーバー起動からAPI連携まで完結します。


## なぜvLLMか


- safetensors直接ロード：GGUF変換の手間が不要です。サーバー起動時にモデルファイルを指定するだけで即時利用できます
- OpenAI互換API標準搭載：base_urlをhttp://localhost:8000/v1に設定すれば、既存のOpenAI SDKコードがそのまま動作します
- NVIDIA独自アーキテクチャ対応：Mamba-2 + Transformerの「nemotron_hハイブリッドアーキテクチャ」をネイティブサポートしています
- トラブルフリー：Ollamaのバグやllama.cppの手動ビルドは不要です。uv pip install vllmとvllm serveの2ステップで完結します


## セットアップ手順


[bash]
# 仮想環境作成とvLLMインストール
uv venv .venv && source .venv/bin/activate
uv pip install vllm

# サーバー起動（32GB VRAM環境向け最適化）
vllm serve nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese \
    --trust-remote-code \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.9 \
    --port 8000
[/bash]

なお、uvはRust製の高速パッケージマネージャで、pipの代替として使用しています。uv pip installはpip installと同じ感覚で使えますが、依存解決が数倍速いです。もちろん通常のpip install vllmでも問題ありません。

起動するとhttp://localhost:8000/v1にOpenAI互換のREST APIが立ち上がります。初回はHuggingFaceからモデルが自動ダウンロードされ、2回目以降はキャッシュから即座にロードされます。RTX 5090環境ではモデルロードからAPI Readyまで約30秒です。


## OpenAI互換APIの威力


既存のOpenAIコードを1行変更するだけでローカルモデルが利用可能です。ストリーミング生成も標準対応しており、APIキーはダミーで問題ありません。

[bash]
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
response = client.chat.completions.create(
    model="nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
    messages=[{"role": "user", "content": "こんにちは"}]
)
print(response.choices[0].message.content)
[/bash]

これが何を意味するかというと、OpenAI SDKを使って書かれた既存のアプリケーションがbase_urlの1行変更だけでローカルLLMに切り替わるということです。APIキー不要、課金ゼロ、データ外部送信なし。この互換性こそがvLLMを選ぶ最大の理由です。


## 実際の活用事例


筆者は実際にこのvLLMサーバー1台を複数のアプリケーションから共有利用しています。以下はすべて実稼働中の事例です。

▼Webチャット（Streamlit + Brave Search RAG）

Brave Search APIで取得した検索結果をコンテキストに注入し、最新情報を踏まえた回答を生成するRAGチャットを構築しました。

[bash]
import streamlit as st
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

if prompt := st.chat_input("質問を入力"):
    # Brave Searchで関連情報を取得
    search_results = brave_search(prompt)

    # 検索結果をコンテキストとして注入
    messages = [
        {"role": "system", "content": f"以下の検索結果を参考に回答:\n{search_results}"},
        {"role": "user", "content": prompt}
    ]

    stream = client.chat.completions.create(
        model="nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
        messages=messages,
        stream=True
    )
    for chunk in stream:
        st.write(chunk.choices[0].delta.content or "", end="")
[/bash]

ローカルLLMなのでAPIコスト0で、検索拡張された回答が得られます。

▼Flutter Web UI + Flask APIによるマルチツール

Flask APIサーバー（port 5001）がvLLMへのプロキシとして機能し、Flutter Webで構築した複数のツールから共有利用しています。

[bash]
# api_server.py（Flask）
VLLM_URL = "http://localhost:8000/v1"

@app.route("/api/llm/stream", methods=["POST"])
def llm_stream():
    data = request.get_json()
    response = requests.post(f"{VLLM_URL}/chat/completions", json={
        "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
        "messages": data["messages"],
        "stream": True
    }, stream=True)
    return Response(response.iter_content(), content_type="text/event-stream")
[/bash]

Flutter Web側には以下のツールを実装しました：
- ブログGenerator：Claude Codeの開発セッションを記事化
- ファイルQ&A：ローカルファイルの内容について質問
- Git Story：コミット履歴を物語風に変換

1つのvLLMサーバーで全ツールが動作します。

▼Claude Code履歴からのブログ自動生成

Claude Codeのセッション履歴（JSONL）をNemotronに食わせてブログ記事を自動生成しています。実際にこの仕組みで以下の記事を生成しました：

- 将棋AI「20BモデルのONNX変換とパラメータチューニング」
- 「READMEを読まない開発者に襲う"幻想の罠"」
- 「PatentLLMの課金システムをStripe Checkoutで実装した話」

開発中の試行錯誤がそのまま記事の素材になるため、「ブログを書く時間がない」問題が解消されます。

▼MinecraftのAIボット

Minecraft内のNPCの「脳」としてNemotronを活用しました。brain.pyがlocalhost:8000に接続し、プレイヤーの状況を基にNPCの行動を生成します。

[bash]
# brain.py
VLLM_URL = "http://localhost:8000/v1/chat/completions"

def get_action(player_state):
    response = requests.post(VLLM_URL, json={
        "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
        "messages": [{"role": "user", "content": f"プレイヤーの状態: {player_state}\n次の行動を決定せよ"}]
    })
    return response.json()["choices"][0]["message"]["content"]
[/bash]

ローカルLLMならではの活用例で、API課金を気にせずNPCに「知性」を与えられます。

▼日報自動生成（cron連携）

毎朝4時にcronで実行し、Claude CodeとGeminiの使用履歴を収集してNemotronが1日のまとめレポートを生成します。

[bash]
# crontab -e
0 4 * * * cd /home/soy/Projects/nemotron-test && .venv/bin/python daily_report.py
[/bash]

生成されたレポートはdaily_reports.dbに蓄積され、開発活動の振り返りに活用しています。

▼コードベース分析パイプライン

自分の全プロジェクト（13個）のPythonコードをNemotronに分析させ、再利用可能なパターンを自動抽出しました。

- コードテンプレート：281件（DB操作、API呼び出し、ファイルI/O等）
- プロンプトパターン：123件（分析、文章生成、システム指示等）
- 出力先：FTS5全文検索対応のknowledge.db

thinkingモードOFF + max_tokens: 64の設定で分類タスクを18件/秒で処理しました。


## Thinkingモードの扱い方


Nemotron 9Bはデフォルトでthinking（推論）モードが有効であり、出力に<think>タグが付く場合とタグなしのpreamble（"Okay, let's see..."）の2パターンがあります。用途に応じた対処法は以下の通りです。

- JSON出力が欲しい場合：chat_template_kwargs: {"enable_thinking": False} で無効化
- テキスト出力の場合：strip_thinking_preamble() で最初の # 見出しまでスキップ
- バッチ分類の場合：thinking OFF + max_tokens: 64 で18件/秒を達成

[bash]
# thinkingモードを無効化する例
response = requests.post(f"{VLLM_URL}/chat/completions", json={
    "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
    "messages": messages,
    "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
})
[/bash]


## Qiita記事との比較まとめ


項目 / Qiita記事（llama.cpp） / 本記事（vLLM）
モデル変換：GGUF変換必要 / 不要（safetensors直接）
バックエンド：llama.cpp手動ビルド / pip install vllm
API：独自サーバー / OpenAI互換（標準搭載）
Ollamaの罠：回避のため手動ビルド / そもそも関係なし
既存コード流用：接続コード書き直し / base_url変更のみ
UI：Open WebUI (Docker) / 自作可能（何でも使える）
GPU要件：GGUF量子化で低VRAM対応 / 24GB以上推奨（bf16）

なお、llama.cppにはGGUF量子化による低VRAM環境への対応というメリットがあります。VRAMが16GB以下の環境ではllama.cppの方が適している場合もあります。本記事のvLLMアプローチは24GB以上のVRAMを持つ環境で最も効果を発揮します。


## まとめ


vLLMなら3行で起動し、OpenAI SDKでそのまま使えます。1台のvLLMサーバーをStreamlitチャット・Flutterツール・Minecraft AI・日報生成・コード分析パイプラインなど複数アプリで共有利用できます。

ローカルLLMの本当の価値は「自分の開発環境に溶け込む」ことです。Ollamaの落とし穴やllama.cppの煩雑さから解放され、base_urlを1行変えるだけで既存のOpenAIコードがローカルモデルで動きます。API課金ゼロ、データ外部送信なし、そしてGPUさえあれば無制限に使えます。この記事が、ローカルLLMを「試してみる」段階から「実際に活用する」段階へ進むきっかけになれば幸いです。

---

この記事はNemotron-Nano-9B-v2-Japanese自身によって生成されました。
