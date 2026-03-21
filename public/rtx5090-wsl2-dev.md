---
title: RTX 5090 + WSL2で構築する個人AI開発環境 — GPU 32GBをフル活用する実践構成
tags:
  - gpu
  - nvidia
  - deeplearning
  - vllm
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---


## なぜRTX 5090 + WSL2か


RTX 5090の32GB VRAMは、大規模LLMモデルをローカルで推論する実用的な選択肢です。RTX 4090（24GB）と比較するとVRAM容量が33%向上し、モデルサイズの拡張余地が増加します。vLLMによるバッチ処理では32GB VRAMをフル活用した並列推論が可能です。

CUDA 12.8ツールキットはPyTorchやtritonと互換性があります。WSL2環境ではWindowsホスト側のGPUドライバーが直接GPUを提供するため、Linuxツールチェーン（vLLM、TensorRT、llama.cpp等）の恩恵を受けられます。


## 環境構成の全体像



### vLLMサーバー（常駐プロセス）


[bash]
systemctl --user enable vllm.service
systemctl --user start vllm.service
[/bash]

- モデル：Nemotron 9B等をFP8で推論します
- gpu-memory-utilizationで使用量を制御します


### TensorRT将棋AI

FP8量子化したモデルをTensorRTで最適化し、高速推論を実現します。


### Streamlitアプリ

LLM推論結果の表示や、検索フォーム等のUIを提供します。


## GPU共有の実態


vLLMサーバーは常駐プロセスとして起動し、CUDA_VISIBLE_DEVICESで特定GPUを指定します。将棋AIを起動する際は、gpu-memory-utilizationパラメータでvLLMの使用量を制限し、リソースを共有します。

切り替え手順は以下の通りです。
- vLLMのメモリ使用量を確認します
- 必要に応じてvLLMサービスを再起動し、メモリ割り当てを調整します
- TensorRTプロセスを起動します


## WSL2固有のハマりポイント



### メモリ上限の設定

WSL2のデフォルトメモリ制限では不足する場合があります。

[bash]
# ~/.wslconfig（Windows側）に追記
[wsl2]
memory=16GB
[/bash]

設定変更後は wsl --shutdown で反映させます。


### ディスクI/Oの遅延

WSL2からWindows側のファイルシステム（/mnt/c/...）はI/O性能が低下します。データファイルはWSL2ディストリビューション内（/home/...）に配置することで、ネイティブLinuxファイルシステムの性能を活用できます。


### systemdサービスの設定

WSL2でsystemdを使用する場合は、/etc/wsl.confに以下を追記します。

[bash]
[boot]
systemd=true
[/bash]

ユーザーサービスを自動起動するには loginctl enable-linger が必要です。


## 実際のワークロード例



### LLM推論（vLLM）


[bash]
python -m vllm.entrypoints.openai.api_server \
  --model nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese \
  --dtype auto \
  --max-model-len 32768
[/bash]


### 将棋AI（TensorRT最適化）

FP8量子化により、VRAMを大幅に節約しつつ高速推論を実現します。


### SQLite FTS5検索

全文検索エンジンを活用した高速なデータ検索も同時に運用可能です。


## まとめ


RTX 5090 + WSL2の組み合わせは、32GB VRAMの全容量をAI開発に特化できる実践的な構成です。WSL2の課題（メモリ上限・ディスクI/O）は設定ファイルの調整で解消可能で、vLLMやTensorRTの最新機能をフル活用できます。データファイルはWSL2内のLinuxファイルシステムに配置することがパフォーマンスの鍵です。

この記事はNemotron-Nano-9B-v2-Japaneseが生成し、Gemini 2.5 Flashが整形・検証を行いました。

---

*元記事: [media.patentllm.org](https://media.patentllm.org/blog/gpu-inference/rtx5090-wsl2-dev)*
