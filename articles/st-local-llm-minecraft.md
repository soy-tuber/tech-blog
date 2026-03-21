---
title: "Minecraft NPCにローカルLLMで脳を実装 — Nemotron + Mineflayer"
emoji: "🔧"
type: "tech"
topics: ["ai", "machinelearning", "llm", "python"]
published: true
canonical_url: "https://media.patentllm.org/blog/ai/local-llm-minecraft"
---


## やりたいこと


従来のMinecraftボットはコマンドベースの動作が主流でしたが、プレイヤーとの自然な会話や状況に応じた判断が課題でした。本記事では、ローカルで動作するLLMをNPCに組み込み、状況認識→判断→行動を自動生成する実装に焦点を当てます。NVIDIAのNemotron 9BモデルをvLLMでローカル実行し、Mineflayerを介してMinecraft世界と連携させ、プレイヤー発話に応じた柔軟な対応を実現します。


## システム構成


本システムは4つのレイヤーで構成されています。

[text]
Minecraftサーバー
  ↓
Mineflayer（Node.jsでMinecraft操作）
  ↓ IPC（WebSocket/stdin）
brain.py（PythonでLLMと連携）
  ↓
vLLM（Nemotron 9Bをローカル実行）
[/text]


### 各コンポーネントの役割

- Mineflayer：Minecraftサーバーと接続し、ブロック操作やチャットイベントを制御するNode.jsライブラリです
- brain.py：状況認識（プレイヤー位置・インベントリなど）を収集し、LLMにコンテキストを送信します
- vLLM：Nemotron 9Bモデルを高速推論します
- IPC層：PythonとNode.js間はWebSocketやstdin/stdoutで通信します。PythonからMineflayerのAPIを直接呼び出すことはできないため、プロセス間通信が必要です


## brain.pyの実装



### 状況認識

Node.js側のMineflayerがワールド状態をJSON形式で収集し、WebSocket経由でPythonに送信します。

[python]
import json
import websockets

async def receive_world_state(ws):
    """Node.jsのMineflayerからワールド状態を受信"""
    data = await ws.recv()
    state = json.loads(data)
    return state  # {"position": [x, y, z], "inventory": [...]}
[/python]


### LLM判断

収集した状態をvLLMに送り、自然言語による判断を取得します。vLLMはOpenAI互換APIを提供しているため、openaiライブラリで接続できます。

[python]
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

def get_llm_decision(state, player_message):
    prompt = f"""現在の状況：
- プレイヤー座標: {state['position']}
- 持ち物: {state['inventory']}
プレイヤーが『{player_message}』と言いました。
適切な行動をJSON形式で指示してください。"""

    response = client.chat.completions.create(
        model="nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=128,
        temperature=0.3
    )
    return response.choices[0].message.content
[/python]


### 行動の実行

LLMの判断結果をJSON形式で受け取り、WebSocket経由でNode.js側のMineflayerにコマンドとして送信します。


## プレイヤー発話への応答


プレイヤーが発話した際の処理フローは以下の通りです。
- MineflayerのchatイベントをNode.js側で検知します
- 状況認識データを収集しWebSocketでPythonに送信します
- brain.pyがvLLMに「会話文脈＋プレイヤー発話」を送信します
- 返答をWebSocket経由でNode.jsに返し、Minecraftチャットに送信します


## ローカルLLMの利点



### API課金なし

vLLMはローカル実行のため月額費用は発生しません。電気代のみで運用可能です。


### vLLMの起動方法


[bash]
docker run --gpus all -p 8000:8000 \
  --env HF_TOKEN="your_huggingface_token" \
  vllm/vllm-openai:latest \
  --model nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.9
[/bash]


## ハマりポイント



### MineflayerはNode.jsライブラリ

MineflayerはNode.jsライブラリのため、PythonからAPIを直接呼び出すことはできません。Node.jsプロジェクトのpackage.jsonでバージョンを管理し、プロセス間通信でPythonと連携する設計が必要です。


### vLLMの認証

Hugging Face Hubのモデルにアクセスする場合はHF_TOKEN環境変数を設定します。


## まとめ


ローカルLLMを活用したMinecraft NPCの知性化は、技術的課題に直面しながらも実現可能です。Nemotronモデルの日本語対応とvLLMの高速推論により、プレイヤーとの自然な対話を実現できます。PythonとNode.js間のIPC設計が実装の鍵となります。

この記事はNemotron-Nano-9B-v2-Japaneseが生成し、Gemini 2.5 Flashが整形・検証を行いました。
