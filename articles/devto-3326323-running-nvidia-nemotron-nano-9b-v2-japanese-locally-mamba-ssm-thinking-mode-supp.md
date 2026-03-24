---
title: "Running NVIDIA Nemotron-Nano-9B-v2-Japanese Locally: Mamba SSM + Thinking Mode Support"
date: 2026-03-08
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-nano-9b-japanese"
devto_url: "https://dev.to/soytuber/running-nvidia-nemotron-nano-9b-v2-japanese-locally-mamba-ssm-thinking-mode-support-5c25"
devto_id: 3326323
---

## NVIDIA Nemotron-Nano-9B-v2-Japanese

This is a 9B parameter LLM specialized for Japanese, released by NVIDIA. It is based on the Mamba SSM (State Space Model) architecture, which efficiently processes long texts using an approach different from Transformers. It also supports Thinking mode (enable_thinking=True), allowing explicit output of the inference process.

## Environment

*   OS: Ubuntu (WSL2)
*   GPU: RTX 5090 (VRAM 32GB)
*   Python: 3.13
*   Package Manager: uv

## Environment Setup

Dependencies are managed using `uv`'s `pyproject.toml`. For `causal_conv1d` and `mamba_ssm`, pre-built `.whl` files from their GitHub release pages are specified.

```bash
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
```

System packages required for building:

```bash
sudo apt install build-essential python3.13-dev
```

Environment setup:

```bash
uv sync
```

## Inference Script

This is an example of inference with Thinking mode enabled. The model is loaded in `bfloat16` and automatically placed on the GPU using `device_map="auto"`.

```python
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
```

## Features of Mamba SSM

Traditional Transformer architectures have an Attention mechanism whose computational complexity scales quadratically with sequence length. Mamba SSM, based on state-space models, can process long sequences in linear time. Despite its relatively small model size of 9B parameters, it achieves high-quality Japanese generation.

Since `causal_conv1d` and `mamba_ssm` include CUDA kernels, it is recommended to use pre-built `.whl` files. Building from source would require the CUDA Toolkit and a build environment.

## Impressions

Being a 9B-class model, the RTX 5090 (32GB) has ample VRAM even when running in `bfloat16`. Running without quantization is advantageous for quality. Thinking mode ensures transparency in inference, making it easier to judge the reliability of the output. Its practicality for Japanese tasks is high.
