---
title: "Using Local LLMs as a \"Batch Processing Engine\" — A Design for Automatically Generating Artifacts from Your Own Data"
date: 2026-03-08
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-batch-engine"
devto_url: "https://dev.to/soytuber/using-local-llms-as-a-batch-processing-engine-a-design-for-automatically-generating-artifacts-12pd"
devto_id: 3326264
---

## Using Local LLMs as a "Batch Processing Engine" — Designing Automated Artifact Generation from Your Own Data with Nemotron

### Introduction

In an era where interacting with AI has become commonplace, the most frequent uses for local LLMs are likely "conversing via a chat UI" or "querying internal documents with RAG." While these applications certainly have value, I felt it was a bit wasteful to dedicate the computational power of a GPU running on my PC solely to them.

Over about half a year of continuous development, I realized there's another way to use local LLMs: integrating them not as a conversational partner, but as a component within a processing pipeline. Imagine leaving it to run in a batch overnight and waking up to find the artifacts already generated. That's the kind of usage I'm talking about.

In this article, I will describe a system that runs NVIDIA's Nemotron with vLLM, scans data residing in my development environment in read-only mode, and outputs analysis results as text files. This system avoids large-scale frameworks or cloud APIs. It's an extremely simple architecture where a Python script merely sends HTTP requests to `localhost:8000`.

### What is Nemotron?

Nemotron, released by NVIDIA, is a family of open models that balance efficiency and accuracy. Its weights, training data, and recipes are all open, and it's available for commercial use. Notably, the Nano series models adopt a hybrid architecture of Mixture-of-Experts (MoE) and Mamba2, achieving high accuracy relative to their parameter count.

The model I'm using this time is Nemotron-Nano-9B-v2-Japanese, a Japanese-specific variant released by NVIDIA in February 2026. This model's origin is not simply a "small 9B model."

First, there's a 12B parameter base model that NVIDIA trained from scratch with approximately 20 trillion tokens using the Nemotron-H architecture (a hybrid of Mamba-2 and Transformer). This was then pruned to a size that can run on a single GPU and compressed to 9B, resulting in Nemotron-Nano-9B-v2-Base. From there, inference traces from DeepSeek R1 and Qwen3-235B were used as synthetic data for post-training, completing the English version of Nemotron-Nano-9B-v2. The model card explicitly states "Improved using Qwen," indicating that it actively incorporates achievements from the open-source community, not just NVIDIA's proprietary technology. The Japanese version further builds upon this by using the Nemotron-Personas-Japan dataset, undergoing continuous pre-training and SFT in Japanese. It achieved first place among models under 10B on the Nejumi Leaderboard 4.

Despite its lightweight 9B parameter size, it can practically handle tasks such as text classification, structuring, and summarization. Running it with vLLM on an RTX 5090, the inference speed is sufficient, completing batch processing of about 100 items in approximately an hour.

Crucially, vLLM provides an OpenAI-compatible API endpoint. By sending a POST request to `localhost:8000/v1/chat/completions`, you receive a response in the exact same JSON format as the OpenAI API. This means that from the script's perspective, it's merely a difference between the URL being `localhost` or `api.openai.com`. By simply switching an environment variable, you can freely move between local and cloud environments, preventing vendor lock-in.

### Core Design: The Funnel Pipeline

The design philosophy of this system is simple, consisting of the following three phases:

In Phase 1, a Python script scans the local file system in read-only mode, extracting only the necessary information. This process compresses hundreds of gigabytes of data down to a few megabytes of text.

In Phase 2, the extracted text is sent to the Nemotron API for "linguistic processing" such as classification, structuring, and templating. The output consists of `.txt` or `.json` files.

In Phase 3, the generated artifacts are validated and corrected using Claude Code (Opus 4.6). Claude Code directly verifies and proofreads whether Nemotron's output matches the actual file system.

This funnel structure serves several purposes:

First, it reduces the amount of data an LLM actually processes by three to four orders of magnitude. Feeding one terabyte of data directly to an LLM is impractical, whether locally or in the cloud. By intelligently filtering with the Phase 1 Python script, only truly essential information is passed to the LLM.

Next, the Nemotron processing in Phase 2 is completed locally, incurring no costs other than electricity. The difference compared to processing everything with cloud APIs would be at least 100 times, even with a conservative estimate. For batch processing run multiple times a month, this would result in significant annual savings.

Finally, by incorporating fact-checking with a high-performance model in Phase 3, we compensate for the local LLM's weakness: hallucinations. 95% of the workload is processed locally, with only the remaining 5% for validation entrusted to Claude Code. This approach allows for high-volume processing with low-cost resources, reserving higher costs solely for quality assurance.

### What Was Built

I will now introduce scripts that are actually running with this design. All of them adhere to the same architecture.

The first is prompt catalog generation. It scans all `.py` files under `projects/`, extracting prompt strings sent to AI APIs using regular expressions. It supports multiple patterns, such as the 'content' key and assignments to `system_prompt` variables. The extracted prompts are sent to Nemotron to be categorized by use case (e.g., code generation, summarization, analysis, classification) and to generate templated versions with variable parts replaced by `{placeholder}`. The output is a catalog of reusable prompts. This automatically creates a "collection of my own prompt patterns" from my codebase.

The second is code template generation. It scans all code files under `Project/` to generate a set of code that can be used for similar future `Project`s.

### Third: Environment Rulebook Generation
We collect OS information, Python versions, `nvidia-smi` output, lists of installed packages, project structures, and configuration files by executing commands, and pass this factual data to Nemotron to format it into a development environment rulebook. Rules such as "use uv," "this CUDA version," and "port assignments are as follows" are generated based on actual environment data. Each rule is accompanied by a reference to its basis, making it easy for Claude Code to cross-reference in Phase 3.

### Fourth: Local Data Cross-Analysis
This combines three functions into a single script: a function to generate a project portfolio from `README.md` files; a function to cross-collect Git configuration files (`.gitconfig`, `.gitignore`, SSH config, `gh CLI` settings) to create a Git operations rulebook; and a function to aggregate the history of bash commands executed by Claude Code and shell history to create a command dictionary.

### Fifth: Dead Code and Unnecessary File Detection
We perform file-level detection of empty files, junk files (`.log`, `.bak`, `.tmp`), duplicate files using MD5 hashes, and isolated `__init__.py` files. Furthermore, we use AST analysis to detect unused imports and uncalled functions. A mechanism to exclude items referenced by other files via cross-referencing has also been implemented. Bloated directories, abandoned `.venv` environments, and cache remnants are also aggregated.

### Sixth: Claude Code Plugin and Skill Analysis
We collect and list MCP server settings from `~/.claude.json` and `.mcp.json`, read `SKILL.md` files under `~/.claude/skills/` to inventory existing skills, and also collect the contents of `CLAUDE.md`. Based on this, Nemotron is prompted to suggest "missing skills" and output drafts in the actual `SKILL.md` format. The generated skill files can be copied directly to `~/.claude/skills/`.

## The Significance of the API Design
As some of you may have realized by now, these scripts only perform three actions: "read files," "make HTTP requests," and "write text files." They do not modify the existing environment in any way. There's no need to install anything with `pip`, nor to change any database schemas. If the vLLM process is stopped, the LLM side returns to a completely clean state.

This is possible because local LLM inference servers provide an "API" as an abstraction layer. Whether it's vLLM, SGLang, or llama.cpp, all of them set up endpoints as HTTP servers and communicate using an OpenAI-compatible JSON format. The script simply sends POST requests using the `requests` library.

This "loose coupling" offers significant freedom. If you want to swap models, you just change the `MODEL` name in the environment variables. Switching the inference server from vLLM to SGLang requires zero script modifications. If you want to switch to a cloud API, you just change the URL. The core Python script, which handles the processing, doesn't need to know any of the LLM's implementation details.

The same OpenAI-compatible API can also be used with Ollama. In fact, the script code runs on Ollama without a single line of change. So why did we choose vLLM? To be honest, the benefits of parallel processing were minimal. Even with an RTX 5090, loading a 9B model limits VRAM availability, so we restricted concurrent requests to one, and instead maximized `max_tokens` to increase the completion rate of outputs. The reasons we continue to use vLLM are its fine-grained control over inference parameters and its stability as a server process. For batch processing left overnight, it's paramount that the process doesn't crash midway.

## Why Nemotron + vLLM? — The Reality of the NVIDIA Stack
One might assume that "Nemotron, CUDA, TensorRT, vLLM — all part of the NVIDIA ecosystem, so they must be perfectly compatible," but the reality is a bit more complex.

The ideal stack might look like this:

- Nemotron (Model)
  - ↓ NVIDIA-made, optimized for NVIDIA GPUs
- TensorRT-LLM (Inference Optimization)
  - ↓ Quantization, kernel fusion, KV cache optimization
- vLLM (Serving)
  - ↓ PagedAttention, scheduling
- CUDA (GPU Computing Foundation)
  - ↓
- RTX 5090 (Hardware)

However, the configuration actually running is this:

- Nemotron → vLLM → PyTorch → CUDA → RTX 5090
  - (TensorRT is not used)

vLLM's default backend is PyTorch + custom CUDA kernels (e.g., FlashAttention), and it does not use TensorRT. NVIDIA has its own serving stack, TensorRT-LLM + Triton Inference Server, which is in competition with vLLM. While using TensorRT-LLM might increase inference speed, it significantly increases setup complexity and requires model conversion (engine build), making it difficult to swap models easily.

What's even more interesting is that Nemotron Nano adopts a hybrid Mamba2 + MoE architecture. Since this differs from standard Transformers, its performance depends on vLLM's support. vLLM has recently added support for Mamba-based models, but the depth of optimization is not as extensive as for Transformers. Similarly, in TensorRT-LLM, support for hybrid architectures is still evolving. In other words, contrary to the image of a "unified NVIDIA stack," what's actually effective are CUDA-level optimizations and vLLM's memory management, not the benefits of TensorRT. Nevertheless, it achieves sufficiently practical speeds thanks to the small 9B model size and the RTX 5090's 32GB VRAM.

## Handling Thinking Output
There was one particular pitfall during implementation. Nemotron Nano has reasoning (thinking) mode enabled by default. The API response directly includes the thought process, such as "Okay, let's tackle this...", followed by the JSON. This was the reason why 87 out of 106 prompt catalog generations failed to parse.

The solution is a bit brute-force but reliable. We'll centralize a function to remove the thinking process from the response text and reuse it across all scripts. If a `<think>` tag is present, its content is removed. If not, the function searches for the last `{...}` block in the text and attempts to parse it as JSON. While there's an option to specify `enable_thinking: false` in the request, some server implementations might ignore it. Therefore, handling it on the parser side is the most robust approach.

## Cost

Let's compare with actual figures.

If all 106 classifications in the prompt catalog were done via cloud API, with several thousand tokens of input/output per item, the total cost would be around a dozen dollars. Adding the environment rulebook, README analysis, command dictionary, dead code detection, and skill analysis would bring a single execution to several tens of dollars.

With a local Nemotron, the only cost is electricity. Running a 9B model on an RTX 5090 consumes very little power, costing only a few yen per batch execution. Only the final check by Claude Code incurs an API fee, but since it only involves reading and correcting several thousand lines of text, it costs just a few hundred yen.

If these scripts are run a few times a month, the annual cost difference could amount to hundreds of thousands of yen. While there's an initial investment in a local GPU, considering it can be shared with other uses like development, gaming, and AI inference, the cost specifically for batch processing is virtually zero.

## The Significance of Local Data

There's another crucial point not to overlook. Data in a development environment often contains sensitive information that you wouldn't want to send externally. This includes API keys, internal project code, client contract files, and personal investment information. While technically possible to send these to a cloud API, practically, one might hesitate.

In a locally-contained pipeline, data never leaves your machine. Both file system scans and inference requests to the LLM are completed entirely on `localhost`. Even when using Claude Code in Phase 3, what's sent is the "artifact" generated by Nemotron, not the original source data.

## Versatility as a Design Pattern

Looking back, the pattern used here is extremely simple:

`File Reading → Extraction/Aggregation → localhost:8000 → sqlite`

By simply swapping out the data source, countless variations can be created. In fact, all five scripts introduced in this article follow this pattern. When creating a new script, you only need to consider three things: "What data?", "How to extract it?", and "What to ask the LLM?" The code for LLM connection and file output can largely be copy-pasted.

I also created a wrapper script called `run_all.py`. It executes multiple scripts sequentially and manages their progress. If interrupted, it resumes from the incomplete script next time. Once all are complete, a summary is displayed for handover to Claude Code. This design is intended for overnight operation.

## Future Extensions

This pipeline can continue to expand horizontally as long as there's a data source. Here are a few ideas:

Chrome's browsing history is stored locally as an SQLite file. By reading this and analyzing search query trends, a timeline of development activities could be created, showing "when something was researched, what it was, and which commit it led to."

vLLM access logs themselves can also be targets for analysis. Which models were used, when, and how much? What are the trends in inference times? Data that could lead to optimizing GPU utilization efficiency lies dormant within the logs.

Cross-sectional analysis of case law databases is also being considered. With 30,000 case law records in SQLite, we could extract cases related to specific themes across the database and automatically generate summaries by point of contention. This would also serve as a test of Nemotron's Japanese language proficiency in handling legal documents.

The US patent database has also grown to nearly 4 million records; although this is in English, it could potentially be organized similarly. Notably, even the cheapest APIs would cost over $1000 per process, so the benefits are substantial.

Looking a bit further ahead, if each stage of this pipeline were to be containerized as an MCP server, we could envision a world where Claude Code itself could simply instruct "Analyze this data with Nemotron," and the entire process would execute automatically. It could also perform periodic patrols. Local LLMs and cloud LLMs would collaborate, each taking on roles in their respective areas of expertise. Such a configuration is not yet widely seen in practice.
