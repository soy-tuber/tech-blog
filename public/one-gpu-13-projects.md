---
title: RTX 5090 1枚で13プロジェクトを回す個人開発者のポートフォリオ戦略
tags:
  - GPU
  - NVIDIA
  - DeepLearning
  - vLLM
private: false
updated_at: '2026-03-21T21:41:13+09:00'
id: da4a08a0ba7eb06f442f
organization_url_name: null
slide: false
ignorePublish: false
---


## 13プロジェクト一覧


ポートフォリオは以下のカテゴリで構成されています。


### 法律関連

- 契約書自動生成ツール（Streamlit + Gemini APIで条項提案）
- 判例検索システム（SQLite FTS5で判例文書を高速検索）
- 法令チェックチャットボット（Geminiで条文解釈支援）


### 化学シミュレーション

- 分子構造予測モデル（FP8量子化ResNet）
- 反応速度計算エンジン（CUDAカーネル最適化済み）


### 将棋AI

- Fuka40B（FP8量子化ResNet40x384、80層）
- Fuka2025Q2-20b（FP8政策評価モデル）
- Floodgate戦略エンジン
- ttzl-ex（TensorRT推論最適化）
- 将棋データ解析パイプライン


### その他

- Minecraft AIアシスタント（vLLM常駐）
- 株式データ可視化ダッシュボード
- 研究ノート管理システム


## 技術スタックの共通化



### 検索基盤：SQLite FTS5

全プロジェクトで検索機能を統一するため、SQLiteのFTS5を採用しています。特許文書や判例データでは、BM25によるランク付けで高速かつ関連度の高い検索を実現しています。


### 共通UI：Streamlit

全アプリのフロントエンドにStreamlitを使用し、Gemini API連携時のレスポンス表示を標準化しています。

[python]
import streamlit as st
from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="特許文書から条項を抽出"
)
st.markdown(f"**提案条項**:\n{response.text}")
[/python]


## GPU共有戦略



### vLLM常駐アーキテクチャ

RTX 5090の32GB VRAMを最大活用するため、vLLMを常駐プロセスとして起動しています。各プロジェクトでモデルサイズに応じて推論エンジンを切り替えます。


### TensorRT切替ロジック

将棋AIではTensorRTでモデルを最適化しています。

[bash]
trtexec \
  --onnx=models/eval/model_fp8.onnx \
  --fp8 \
  --minShapes=input1:1x62x9x9,input2:1x57x9x9 \
  --optShapes=input1:256x62x9x9,input2:256x57x9x9 \
  --maxShapes=input1:256x62x9x9,input2:256x57x9x9 \
  --saveEngine=model_fp8_trt
[/bash]


### GPU使用率監視


[bash]
while true; do
  usage=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | tr -d ' ')
  if [ "$usage" -gt 80 ]; then
    systemctl --user stop vllm.service
  fi
  sleep 60
done
[/bash]


## Cloudflare + Caddy公開基盤


すべてのWebプロジェクトをCloudflare Tunnel + Caddyで公開しています。Caddyがリバースプロキシとして機能し、HTTPS終端とルーティングを担当します。


## セキュリティの横展開


全プロジェクトで共通のセキュリティポリシーを適用しています。
- APIキーは環境変数で管理し、コードにハードコードしません
- ブランチ保護でPR必須設定としています
- 定期的なログ監査スクリプトを自動実行しています


## 運用のコツ


- CUDA 12.8に統一し、プロジェクト間のバージョン競合を解消しました
- 環境変数でプロジェクトごとのライブラリパスを管理しています
- GPU使用率閾値超過時に自動でサービスを停止します


## まとめ


RTX 5090の32GB VRAMを最大活用するため、以下の3点を最優先しました。
- 共通基盤の構築：SQLite FTS5とStreamlitで検索・UIを統一しました
- 動的リソース管理：vLLM + TensorRT切替でモデル負荷に応じた最適化を行っています
- セキュリティの横展開：認証プロセスを標準化しました

特に将棋AIプロジェクトでは、FP8量子化とTensorRTの組み合わせにより、FP16比で大幅な推論速度向上を実現しました。個人開発では「技術選定の自由度」と「共通基盤の重要性」のバランスが成功の鍵です。

この記事はNemotron-Nano-9B-v2-Japaneseが生成し、Gemini 2.5 Flashが整形・検証を行いました。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/gpu-inference/one-gpu-13-projects)*
