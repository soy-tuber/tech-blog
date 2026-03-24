---
title: "vLLM vs TensorRT-LLM vs Ollama vs llama.cpp — Choosing the Right Inference Engine on RTX 5090"
date: 2026-03-14
topics: ["ai", "llm", "nvidia", "deeplearning"]
published: true
canonical_url: "https://dev.to/soytuber/vllm-vs-tensorrt-llm-vs-ollama-vs-llamacpp-choosing-the-right-inference-engine-on-rtx-5090-2aap"
devto_url: "https://dev.to/soytuber/vllm-vs-tensorrt-llm-vs-ollama-vs-llamacpp-choosing-the-right-inference-engine-on-rtx-5090-2aap"
devto_id: 3351543
---

## Why This Comparison Exists

I've been running Nemotron Nano 9B v2 Japanese on an RTX 5090 with vLLM 0.15.1 for months now. Before settling on vLLM, I evaluated TensorRT-LLM, considered Ollama, and benchmarked llama.cpp. This article captures what I learned — not from reading docs, but from actually trying to get each engine running on consumer Blackwell hardware.

The short version: **vLLM won.** But the reasons are more nuanced than "it's the best." Each engine occupies a different niche, and the right choice depends entirely on your hardware, model architecture, and use case.

## The Four Contenders at a Glance

| Feature | vLLM | TensorRT-LLM | Ollama | llama.cpp |
|---|---|---|---|---|
| **Primary focus** | Production serving | Maximum throughput | Simplicity | Portability |
| **Quantization** | AWQ, GPTQ, BF16, FP8 | FP8, FP4, INT8 | GGUF (via llama.cpp) | GGUF (Q4_K_M, Q5_K_M, etc.) |
| **API** | OpenAI-compatible | Custom + Triton | OpenAI-compatible | OpenAI-compatible (server mode) |
| **Setup difficulty** | Medium (source build for 5090) | Hard (Docker/NGC required) | Trivial (`curl + ollama run`) | Easy (`cmake + make`) |
| **RTX 5090 support** | Yes (v0.15.1+) | Partial (SM120 kernel gaps) | Yes | Yes |
| **Continuous batching** | Yes (PagedAttention) | Yes (inflight batching) | No | No |
| **Mamba/SSM support** | Yes | Limited | Via GGUF only | Via GGUF only |

## vLLM: The Pragmatic Choice

### What It Does Well

vLLM's core innovation is **PagedAttention** — treating KV cache like virtual memory pages. This eliminates the memory waste that plagues naive implementations and enables efficient continuous batching. On my RTX 5090 running Nemotron 9B in BF16:

- **Single request**: ~83 tok/s
- **TTFT**: 45–60 ms
- **Batched (10 concurrent)**: ~630 tok/s
- **VRAM usage**: 30.6 / 32 GB

That batched throughput — 7.5x single-request speed — is the real story. If you're serving multiple users or running batch processing pipelines, this matters enormously.

### The OpenAI-Compatible API

vLLM exposes a drop-in replacement for the OpenAI API. Every tool in the Python ecosystem that speaks OpenAI's protocol — LangChain, LlamaIndex, custom clients — just works:

```bash
vllm serve nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese \
    --trust-remote-code \
    --reasoning-parser-plugin nemotron_nano_v2_reasoning_parser.py \
    --reasoning-parser nemotron_nano_v2 \
    --max-num-seqs 64 \
    --mamba_ssm_cache_dtype float32
```

Then from any client:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
response = client.chat.completions.create(
    model="nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
    messages=[{"role": "user", "content": "Explain PagedAttention"}],
    max_tokens=1024
)
```

### The Pain Point: Installation on RTX 5090

Let's be honest — installing vLLM on Blackwell consumer GPUs was painful in early 2025. A simple `pip install vllm` failed because PyTorch didn't support SM120 (Blackwell's compute capability). You needed nightly PyTorch builds, CUDA 12.8+, and sometimes source compilation.

As of March 2026 with vLLM 0.17+, the situation has improved significantly. The CUDA 13 nightly wheel stack works out of the box. But if you're on an older setup, expect to spend an afternoon wrestling with dependencies.

### Why It Won for My Setup

Nemotron uses a **Mamba-hybrid architecture** (SSM + Transformer layers). vLLM has native Mamba support via `--mamba_ssm_cache_dtype float32`. This was the decisive factor — none of the alternatives handled this architecture as cleanly.

## TensorRT-LLM: Faster, but at What Cost?

### Raw Performance

TensorRT-LLM is genuinely faster in raw throughput — **20–100% depending on quantization** — and FP8 support is its biggest advantage. On H100 clusters with pure Transformer models, it's the undisputed king:

- Batch-128 throughput on 8×H100: ~4,800 tok/s (vs vLLM's ~3,400 tok/s)
- TTFT at batch-1: <10 ms
- FP4 quantization on Blackwell data center GPUs: exceptional

### Why I Skipped It

For my RTX 5090 setup, TRT-LLM didn't make sense for four specific reasons:

1. **Mamba-hybrid architecture support is still rough.** TRT-LLM's Mamba2 support is limited, and Nemotron's hybrid architecture hit edge cases that produced incorrect outputs.

2. **RTX 5090 FP8 kernel support wasn't there** when I evaluated. Consumer Blackwell (SM120) kernels lagged behind data center Blackwell. Error messages like "Fall back to unfused MHA for data_type = bf16... in sm_120" were common.

3. **Installation is Docker-or-bust.** The recommended path is an NGC container. Building from source requires NVIDIA's internal build system knowledge. For a solo developer on WSL2, this adds friction that vLLM doesn't have.

4. **The speed gain at BF16 (no quantization) shrinks to ~10–30%.** Without FP8, vLLM's 630 tok/s batched throughput was already sufficient for my workload.

### When TRT-LLM Makes Sense

- You're running **pure Transformer models** (not Mamba-hybrid)
- You have **H100/H200/B200** data center GPUs
- You need **FP8 or FP4 quantization** for maximum throughput
- You have a team that can handle the DevOps complexity
- You're optimizing for **cost-per-token at scale**

If you're a solo developer on consumer Blackwell hardware running Mamba-hybrid models, TRT-LLM is not the pragmatic choice — at least not yet.

## Ollama: Great for Demos, Wrong for Production

### What It Does Well

Ollama is the **`apt install` of LLM inference**. One command to install, one command to run:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama run llama3:8b
```

It wraps llama.cpp internally, provides a clean CLI, and maintains a model library that makes downloading models trivial. For trying out a new model in 30 seconds, nothing beats it.

### Why It's Not Enough for Serious Work

1. **No continuous batching.** Ollama serves one request at a time. If you're building a pipeline that sends multiple concurrent requests, throughput collapses. My vLLM setup handles 10 concurrent requests at 630 tok/s total; Ollama would serve them sequentially at ~83 tok/s each.

2. **GGUF only.** Ollama uses llama.cpp's GGUF format exclusively. This means no native BF16/FP16 inference, no AWQ/GPTQ, and no PagedAttention. You're limited to the quantization levels GGUF supports.

3. **No Mamba/SSM support** beyond what's available in GGUF format. Nemotron's hybrid architecture doesn't work well through the GGUF conversion pipeline.

4. **Limited GPU utilization.** Without continuous batching, your $2000 GPU sits mostly idle between tokens. On an RTX 5090 with 1.79 TB/s memory bandwidth, this is a waste.

5. **No speculative decoding, no tensor parallelism, no prefix caching.** The advanced serving features that make vLLM and TRT-LLM production-ready are simply absent.

### When Ollama Makes Sense

- Quick model evaluation and experimentation
- Personal chatbot for interactive use (one user, one conversation)
- Machines without CUDA (Ollama supports CPU and Apple Silicon)
- You don't want to think about Python environments or CUDA versions

## llama.cpp: The Swiss Army Knife

### What It Does Well

llama.cpp is the foundation that Ollama builds on, but with full control exposed. Its GGUF quantization format is remarkably efficient — a Q4_K_M quantized 70B model fits in ~40GB, runnable across two RTX 5090s.

Key strengths:
- **CPU/GPU hybrid inference**: Split layers between GPU VRAM and system RAM
- **Broad hardware support**: CUDA, Vulkan, Metal, CPU — runs everywhere
- **Excellent quantization**: Q4_K_M, Q5_K_M, Q6_K offer good quality/size tradeoffs
- **Active development**: The most actively maintained inference project on GitHub

### RTX 5090 Performance (llama.cpp)

Community benchmarks show strong single-GPU numbers:

- **8B models**: ~185–213 tok/s (token generation)
- **32B models**: ~61 tok/s
- **Prompt processing (8B)**: 10,400+ tok/s prefill
- **147K context on 30B MoE**: Stable at ~52 tok/s

These are competitive numbers for single-request inference. The 1.79 TB/s GDDR7 bandwidth of the RTX 5090 is a huge advantage for the memory-bound token generation phase.

### Why It Wasn't Right for My Setup

1. **No continuous batching in the server.** Like Ollama, llama.cpp's server mode handles requests sequentially. For a multi-service architecture where multiple apps query the same model, this is a bottleneck.

2. **GGUF conversion quality for Mamba-hybrid models is uncertain.** Converting Nemotron's mixed SSM/Transformer architecture to GGUF risks losing accuracy in ways that are hard to verify without extensive benchmarking.

3. **No native OpenAI-compatible reasoning parser.** vLLM's plugin system let me write a custom reasoning parser for Nemotron's thinking tokens. llama.cpp's server has more limited extensibility.

4. **Lower batched throughput.** While single-request speed is excellent, the lack of PagedAttention means multi-user serving is fundamentally less efficient.

### When llama.cpp Makes Sense

- **CPU-only or hybrid CPU/GPU** inference (models too large for VRAM)
- **Cross-platform deployment** (macOS, Windows, Linux, even Android)
- **Edge/embedded** scenarios where vLLM's Python stack is too heavy
- **Quantization experimentation** (GGUF offers the widest range of quant levels)
- **Single-user interactive chat** where batching doesn't matter

## The Decision Matrix

| Your Situation | Best Choice | Why |
|---|---|---|
| Production API serving, multiple concurrent users | **vLLM** | PagedAttention, continuous batching, OpenAI API |
| Maximum tok/s on H100/B200, pure Transformer | **TensorRT-LLM** | 35–50% faster raw throughput, FP8/FP4 |
| Quick model testing, personal chatbot | **Ollama** | Zero setup, model library, just works |
| CPU/GPU hybrid, cross-platform, edge deployment | **llama.cpp** | Runs anywhere, efficient quantization |
| Mamba-hybrid models on consumer Blackwell | **vLLM** | Native SSM support, manageable setup |
| Solo dev, RTX 5090, need OpenAI API | **vLLM** | Best balance of performance and usability |

## My Stack: How It All Fits Together

```plaintext
RTX 5090 (32GB VRAM)
    └── vLLM 0.15.1
        └── Nemotron Nano 9B v2 Japanese (BF16)
            ├── PatentLLM (patent search + RAG)
            ├── Hanrei-DB (case law search + summarization)
            ├── Shogi AI evaluation pipeline
            └── Media site translation
```

All services hit the same vLLM instance via OpenAI-compatible API. Continuous batching handles concurrent requests from multiple apps without dedicated GPU allocation per service. One GPU, one inference engine, 13+ projects.

## Conclusion

The LLM inference engine landscape has consolidated around a clear hierarchy:

- **vLLM** for flexible production serving (85% of open-model inference in production uses vLLM, TRT-LLM, or TGI)
- **TensorRT-LLM** for maximum NVIDIA-optimized throughput
- **llama.cpp** for portability and edge deployment
- **Ollama** for frictionless experimentation

For a solo developer on consumer Blackwell hardware running Mamba-hybrid models, **vLLM is the pragmatic choice**. TRT-LLM's raw speed advantage doesn't justify its complexity when your bottleneck is architecture support, not tokens per second. And Ollama/llama.cpp, while excellent tools, lack the serving features that make a single GPU serve an entire project portfolio.

The gap between these engines continues to narrow. TRT-LLM's lead has shrunk from 2–3x to 35–50%, and vLLM's installation story on Blackwell is finally improving. By the time you read this, some of these pain points may already be resolved. But the architectural differences — continuous batching, PagedAttention, native SSM support — are fundamental design choices that won't converge anytime soon.

Choose the engine that matches your actual constraints, not the one with the highest benchmark number.
