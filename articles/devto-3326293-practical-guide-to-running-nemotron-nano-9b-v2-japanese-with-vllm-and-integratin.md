---
title: "Practical Guide to Running Nemotron-Nano-9B-v2-Japanese with vLLM and Integrating it into Your Custom Application via an Open..."
date: 2026-03-08
topics: ["ai", "gpu", "performance"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/gpu-inference/nemotron-vllm-guide"
devto_url: "https://dev.to/soytuber/practical-guide-to-running-nemotron-nano-9b-v2-japanese-with-vllm-and-integrating-it-into-your-klj"
devto_id: 3326293
---

## Introduction

Recently, an article on Qiita titled "Running Nemotron-Nano-9B-v2-Japanese with llama.cpp" gained significant attention. That article required manual building of llama.cpp and GGUF conversion as a workaround for Ollama's zero-division bug, but this article introduces a simpler and more practical approach: "vLLM + OpenAI-compatible API." Using vLLM eliminates the need for GGUF conversion, avoids Ollama-related issues, and allows for direct reuse of existing code. The entire process, from server startup to API integration, can be completed with just three commands.

## Why vLLM?

- **Direct safetensors loading**: Eliminates the hassle of GGUF conversion. Models can be used immediately by simply specifying the model file at server startup.
- **Standard OpenAI-compatible API**: By setting `base_url` to `http://localhost:8000/v1`, existing OpenAI SDK code works out-of-the-box.
- **NVIDIA proprietary architecture support**: Natively supports the "nemotron_h hybrid architecture" of Mamba-2 + Transformer.
- **Trouble-free**: No need for Ollama bugs or manual llama.cpp builds. It's a simple two-step process: `uv pip install vllm` and `vllm serve`.

## Setup Procedure

```bash
# Create virtual environment and install vLLM
uv venv .venv && source .venv/bin/activate
uv pip install vllm

# Start server (optimized for 32GB VRAM environments)
vllm serve nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese \
    --trust-remote-code \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.9 \
    --port 8000
```

Note that `uv` is a fast package manager written in Rust, used here as an alternative to `pip`. `uv pip install` can be used just like `pip install`, but dependency resolution is several times faster. Of course, `pip install vllm` also works without issues.

Upon startup, an OpenAI-compatible REST API will be available at `http://localhost:8000/v1`. The model will be automatically downloaded from HuggingFace the first time, and loaded instantly from the cache on subsequent runs. In an RTX 5090 environment, it takes approximately 30 seconds from model loading to API Ready.

## The Power of OpenAI-Compatible API

Local models can be utilized by changing just one line of existing OpenAI code. Streaming generation is also supported by default, and a dummy API key is sufficient.

```bash
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
response = client.chat.completions.create(
    model="nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
    messages=[{"role": "user", "content": "こんにちは"}]
)
print(response.choices[0].message.content)
```

What this means is that existing applications written using the OpenAI SDK can switch to a local LLM with just a one-line change to the `base_url`. No API key required, zero cost, no external data transmission. This compatibility is the biggest reason to choose vLLM.

## Real-World Use Cases

I actually use a single vLLM server shared across multiple applications. All of the following are examples currently in production.

### Web Chat (Streamlit + Brave Search RAG)

I built a RAG chat that injects search results obtained from the Brave Search API into the context to generate answers based on the latest information.

```bash
import streamlit as st
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

if prompt := st.chat_input("質問を入力"):
    # Retrieve relevant information with Brave Search
    search_results = brave_search(prompt)

    # Inject search results as context
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
```

Since it's a local LLM, there are zero API costs, and you get search-augmented answers.

### Multi-tool with Flutter Web UI + Flask API

A Flask API server (port 5001) acts as a proxy to vLLM, shared and utilized by multiple tools built with Flutter Web.

```bash
# api_server.py（Flask）
VLLM_URL = "http://localhost:8000/v1"
```

```python
@app.route("/api/llm/stream", methods=["POST"])
def llm_stream():
    data = request.get_json()
    response = requests.post(f"{VLLM_URL}/chat/completions", json={
        "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
        "messages": data["messages"],
        "stream": True
    }, stream=True)
    return Response(response.iter_content(), content_type="text/event-stream")
```

The following tools were implemented on the Flutter Web side:
*   Blog Generator: Converts Claude Code development sessions into articles
*   File Q&A: Asks questions about the content of local files
*   Git Story: Transforms commit history into a narrative

All tools operate on a single vLLM server.

### Automatic Blog Generation from Claude Code History

We automatically generate blog posts by feeding Nemotron the session history (JSONL) from Claude Code. This mechanism was actually used to generate the following articles:

*   Shogi AI: "ONNX Conversion and Parameter Tuning for a 20B Model"
*   "The "Illusion Trap" that Befalls Developers Who Don't Read READMEs"
*   "Implementing PatentLLM's Billing System with Stripe Checkout"

Since the trial and error during development directly becomes material for articles, the problem of "not having time to write blog posts" is resolved.

### Minecraft AI Bot

Nemotron was utilized as the "brain" for NPCs in Minecraft. brain.py connects to localhost:8000 and generates NPC actions based on the player's situation.

```bash
# brain.py
VLLM_URL = "http://localhost:8000/v1/chat/completions"

def get_action(player_state):
    response = requests.post(VLLM_URL, json={
        "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
        "messages": [{"role": "user", "content": f"プレイヤーの状態: {player_state}\n次の行動を決定せよ"}]
    })
    return response.json()["choices"][0]["message"]["content"]
```

This is a unique application of a local LLM, allowing us to imbue NPCs with "intelligence" without worrying about API costs.

### Daily Report Auto-Generation (cron Integration)

Executed by cron at 4 AM every morning, Nemotron collects usage history from Claude Code and Gemini to generate a daily summary report.

```bash
# crontab -e
0 4 * * * cd /home/soy/Projects/nemotron-test && .venv/bin/python daily_report.py
```

The generated reports are stored in daily_reports.db and used for reviewing development activities.

### Codebase Analysis Pipeline

I had Nemotron analyze the Python code from all my projects (13 of them) and automatically extract reusable patterns.

*   Code Templates: 281 items (DB operations, API calls, file I/O, etc.)
*   Prompt Patterns: 123 items (analysis, text generation, system instructions, etc.)
*   Output Destination: knowledge.db with FTS5 full-text search support

With thinking mode OFF and max_tokens: 64, classification tasks were processed at 18 items/second.

## Handling Thinking Mode

Nemotron 9B has thinking (inference) mode enabled by default, resulting in two output patterns: one with `<think>` tags and another with a tag-less preamble ("Okay, let's see..."). The countermeasures for different use cases are as follows:

*   For JSON output: Disable with `chat_template_kwargs: {"enable_thinking": False}`
*   For text output: Skip to the first `#` heading with `strip_thinking_preamble()`
*   For batch classification: Achieved 18 items/second with thinking OFF + `max_tokens: 64`

```bash
# Example of disabling thinking mode
response = requests.post(f"{VLLM_URL}/chat/completions", json={
    "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
    "messages": messages,
    "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
})
```

## Comparison Summary with Qiita Article

| Item                  | Qiita Article (llama.cpp)         | This Article (vLLM)                 |
| :-------------------- | :-------------------------------- | :---------------------------------- |
| Model Conversion      | GGUF conversion required          | Not required (direct safetensors)   |
| Backend               | llama.cpp manual build            | `pip install vllm`                  |
| API                   | Custom server                     | OpenAI compatible (standard)        |
| Ollama Trap           | Manual build to avoid             | Not relevant at all                 |
| Existing Code Reuse   | Connection code rewrite           | Only `base_url` change              |
| UI                    | Open WebUI (Docker)               | Customizable (anything can be used) |
| GPU Requirements      | Low VRAM support with GGUF quantization | 24GB+ recommended (bf16)            |

It's worth noting that llama.cpp has the advantage of supporting low VRAM environments through GGUF quantization. For environments with 16GB VRAM or less, llama.cpp might be more suitable. The vLLM approach in this article is most effective in environments with 24GB or more VRAM.

## Summary

vLLM can be launched in 3 lines and used directly with the OpenAI SDK. A single vLLM server can be shared and utilized by multiple applications such as Streamlit chat, Flutter tools, Minecraft AI, daily report generation, and code analysis pipelines.

The true value of local LLMs lies in their ability to "integrate seamlessly into your development environment." You're freed from the pitfalls of Ollama and the complexities of llama.cpp; your existing OpenAI code will run with local models by simply changing one line of `base_url`. Enjoy zero API charges, no external data transmission, and unlimited usage as long as you have a GPU. I hope this article helps you move from merely "trying out" local LLMs to "actually leveraging" them in your work.

---

This article was generated by Nemotron-Nano-9B-v2-Japanese itself.
