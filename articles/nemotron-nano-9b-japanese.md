---
title: "Nemotron 9B日本語をローカルで動かす — Mamba SSM・Thinkingモード対応"
emoji: "🔧"
type: "tech"
topics: ["ai", "machinelearning", "llm", "python"]
published: true
canonical_url: "https://media.patentllm.org/blog/ai/nemotron-nano-9b-japanese"
---


## NVIDIA Nemotron-Nano-9B-v2-Japanese


NVIDIAが公開した日本語特化の9BパラメータLLMです。Mamba SSM（State Space Model）アーキテクチャをベースにしており、Transformerとは異なるアプローチで長文処理を効率化しています。Thinkingモード（enable_thinking=True）にも対応し、推論過程を明示的に出力できます。


## 環境


- OS: Ubuntu（WSL2）
- GPU: RTX 5090（VRAM 32GB）
- Python: 3.13
- パッケージ管理: uv


## 環境構築


uvのpyproject.tomlで依存関係を管理します。causal_conv1dとmamba_ssmはGitHubリリースページの事前ビルドwhlを指定します。

[bash]
[project]
name = "nemotron"
version = "0.1.0"
requires-python = "==3.13.*"
dependencies = [
    "accelerate==1.12.0",
    "causal_conv1d",
    "hf-xet==1.2.0",
    "mamba_ssm",
    "torch==2.7.1+cu128",
    "transformers==4.48.3",
    "triton==3.3.1"
]

[[tool.uv.index]]
name = "torch-cuda"
url = "https://download.pytorch.org/whl/cu128"
explicit = true

[tool.uv.sources]
torch = [{ index = "torch-cuda" }]
causal_conv1d = { url = "https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.6.0/causal_conv1d-1.6.0+cu12torch2.7cxx11abiTRUE-cp313-cp313-linux_x86_64.whl" }
mamba_ssm = { url = "https://github.com/state-spaces/mamba/releases/download/v2.3.0/mamba_ssm-2.3.0+cu12torch2.7cxx11abiTRUE-cp313-cp313-linux_x86_64.whl" }
[/bash]

ビルドに必要なシステムパッケージ：

[bash]
sudo apt install build-essential python3.13-dev
[/bash]

環境構築：

[bash]
uv sync
[/bash]


## 推論スクリプト


Thinkingモードを有効にして推論する例です。bfloat16で読み込み、device_map="auto"でGPUに自動配置します。

[bash]
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    device_map="auto",
)

messages = [{"role": "user", "content": "GPUについて俳句を書いてください"}]

inputs = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    enable_thinking=True,
    return_tensors="pt",
).to(model.device)

outputs = model.generate(inputs, max_new_tokens=128, eos_token_id=tokenizer.eos_token_id)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
[/bash]


## Mamba SSMの特徴


従来のTransformerアーキテクチャはAttention機構の計算量がシーケンス長の二乗に比例します。Mamba SSMは状態空間モデルに基づき、線形時間で長いシーケンスを処理できます。9Bパラメータという比較的小さなモデルサイズでありながら、日本語の生成品質が高いです。

causal_conv1dとmamba_ssmはCUDAカーネルを含むため、事前ビルド済みwhlの使用を推奨します。ソースからのビルドにはCUDA Toolkitとビルド環境が必要になります。


## 所感


9Bクラスのため、RTX 5090（32GB）ではbfloat16のままでもVRAMに余裕があります。量子化なしで動作するのは品質面で有利です。Thinkingモードにより推論の透明性が確保でき、出力の信頼性を判断しやすいです。日本語タスクでの実用性は高いです。
