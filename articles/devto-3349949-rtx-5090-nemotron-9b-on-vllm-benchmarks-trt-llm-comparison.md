---
title: "RTX 5090 + Nemotron 9B on vLLM — Benchmarks & TRT-LLM Comparison"
date: 2026-03-14
topics: ["ai", "gpu", "performance"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/gpu-inference/nemotron-vllm-rtx5090"
devto_url: "https://dev.to/soytuber/rtx-5090-nemotron-9b-on-vllm-benchmarks-trt-llm-comparison-398o"
devto_id: 3349949
---

I've been running Nemotron Nano 9B v2 Japanese on an RTX 5090 with vLLM 0.15.1 and wanted to share some findings that took me a while to figure out — hopefully saves someone else the headache.

■ Benchmarks (RTX 5090, BF16, No Quantization)

All numbers measured on RTX 5090 (32 GB VRAM), running Nemotron Nano 9B v2 Japanese in BF16 precision with no quantization applied.

・Single request: ~83 tok/s
・TTFT (Time to First Token): 45–60 ms
・Batched (10 concurrent requests): ~630 tok/s
・VRAM usage: 30.6 / 32 GB

Batch throughput is roughly 7.5x single — which is what you'd hope for but nice to confirm empirically.

■ Reasoning Parser Fix (vLLM 0.15.1)

The official nemotron_nano_v2_reasoning_parser.py plugin from HuggingFace has a broken import path. The original code references:

[bash]
from vllm.entrypoints.openai.protocol import (
    ChatCompletionRequest,
    DeltaMessage,
    ResponsesRequest,
)
[/bash]

This module doesn't exist in vLLM 0.15.1. The fix:

[bash]
from vllm.entrypoints.openai.chat_completion.protocol import ChatCompletionRequest
from vllm.entrypoints.openai.engine.protocol import DeltaMessage
from vllm.entrypoints.openai.responses.protocol import ResponsesRequest
[/bash]

Without this fix, vLLM crashes on startup with ModuleNotFoundError.

■ max_tokens Gotcha

If you enable reasoning and set max_tokens below ~1024, you'll get content: null in the response with no obvious error message. The thinking tokens eat up the entire budget before the model can produce an actual answer.

Minimum max_tokens: 1024 when reasoning is enabled.

■ Thinking Budget Control

You can limit thinking tokens to speed up responses without killing quality. At max_thinking_tokens=128, I measured Jaster-like accuracy of 0.9/1.0 vs 1.0/1.0 unlimited — a good tradeoff for latency-sensitive applications. See the HuggingFace model card for the ThinkingBudgetClient implementation.

■ Why I Skipped TRT-LLM

TRT-LLM is genuinely faster in raw throughput — 20–100% depending on quantization — and FP8 support is its biggest advantage. But for my setup it didn't make sense:

・Nemotron uses a Mamba-hybrid architecture, and TRT-LLM's Mamba2 support is still limited
・Without FP8 quantization (I'm staying BF16), the speed gain shrinks to ~10–30%
・vLLM 0.15.1 batch throughput (630 tok/s) is already sufficient for my workload
・vLLM's OpenAI-compatible API and Python ecosystem integration is just easier to work with

If you're running a pure transformer model with FP8 on an H100, TRT-LLM probably wins. For Mamba-hybrid on consumer Blackwell hardware at BF16, vLLM is the pragmatic choice right now.

■ Launch Command

[bash]
vllm serve nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese \
    --trust-remote-code \
    --reasoning-parser-plugin nemotron_nano_v2_reasoning_parser.py \
    --reasoning-parser nemotron_nano_v2 \
    --max-num-seqs 64 \
    --mamba_ssm_cache_dtype float32
[/bash]

--mamba_ssm_cache_dtype float32 is important — without it, model accuracy degrades.
