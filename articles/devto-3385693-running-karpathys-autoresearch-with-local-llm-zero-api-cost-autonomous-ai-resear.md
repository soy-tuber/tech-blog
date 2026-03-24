---
title: "Running Karpathy's autoresearch with Local LLM — Zero API Cost Autonomous AI Research"
date: 2026-03-22
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/autoresearch-local-llm-karpathy"
devto_url: "https://dev.to/soytuber/running-karpathys-autoresearch-with-local-llm-zero-api-cost-autonomous-ai-research-41bj"
devto_id: 3385693
---

## Introduction

Andrej Karpathy (OpenAI co-founder) released **autoresearch** — an experiment where an LLM autonomously modifies a GPT training script, runs 5-minute experiments, keeps what improves val_bpb, and discards what doesn't. The original uses Claude Code (cloud API) as the researcher.

[SohniSwatantra's fork](https://github.com/SohniSwatantra/autoresearch-local-llm) replaces Claude Code with **Qwen 3.5 9B running locally via ollama**. Single GPU, zero API cost, fully autonomous.

## Architecture: LLM + Training on One GPU

The key innovation is running both the LLM agent and GPT training on the same GPU:

```plaintext
GPU (48GB VRAM)
├── Qwen 3.5 9B via ollama (~12GB)
└── GPT training via train.py (~35GB)
```

To fit within VRAM constraints, hyperparameters are adjusted from the original:

| Component | Original | This Fork |
|-----------|----------|-----------|
| Depth | 8 layers | 4 layers |
| Device batch size | 128 | 64 |
| Total batch tokens | 524K | 65K |
| Window pattern | SSSL | L |

The model is smaller, but the agent compensates by running more experiments.

## The Autonomous Research Loop

### Step 1: LLM Proposes a Modification

`agent.py` sends the current `train.py` code and experiment history (`results.tsv`) to Qwen 3.5. The LLM proposes specific code modifications to lower val_bpb.

The prompt includes clear constraints:
- Only `train.py` can be modified (`prepare.py` is read-only)
- No new package installations
- Fixed 5-minute time budget
- ~35GB VRAM available for training

### Step 2: Syntax Validation + Git Commit

The proposed code is validated with `ast.parse()`. If valid, `train.py` is overwritten and git committed.

### Step 3: Run 5-Minute Experiment

`uv run train.py` executes with a 10-minute timeout (normally completes in 5 minutes).

### Step 4: Keep or Discard

- val_bpb improved → **keep** (branch advances)
- val_bpb same or worse → **discard** (`git reset --hard`)
- Crash → **crash** (log included in next prompt for LLM to fix)

A failsafe resets to baseline after 3 consecutive crashes.

## agent.py Design

The entire agent is ~250 lines in a single file:

- Ollama API calls (simple `requests.post`)
- Git operations (commit, reset, rev-parse)
- Experiment execution and log parsing
- Results logging to TSV
- Code block extraction from LLM responses

The code extraction pipeline is elegant — regex finds Python code blocks, `ast.parse()` validates syntax, only valid code proceeds to experimentation:

```python
def extract_code_from_response(response):
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", response, re.DOTALL)
    if blocks:
        return max(blocks, key=len)  # Take the longest code block
```

## Cost Comparison

| Setup | Cost per experiment | 100 experiments |
|-------|-------------------|-----------------|
| Original (Claude Code API) | ~$0.05-0.20 | $5-20 |
| This fork (Nosana Pro 6000) | $0.08 | ~$8 |
| This fork (own GPU) | $0 | $0 |

## program.md — The Research Philosophy

Karpathy's original `program.md` contains key design philosophies:

- **"NEVER STOP"** — Run indefinitely until manually stopped
- **Simplicity criterion** — A 0.001 improvement requiring 20 lines of hacky code? Not worth it. Code deletion with equal results? Definitely keep.
- **Assume the user is sleeping** — At 5 min/experiment, that's 12/hour, ~100 experiments during 8 hours of sleep

This is the essence of autoresearch: **let AI do research while you sleep**.

## Why Local LLM Matters

This fork demonstrates that:
- Qwen 3.5 9B (a 9B parameter model) can sustain autonomous ML research loops
- No rate limits or API costs — run infinitely
- Anyone with a 24GB+ GPU can automate their own research

## Setup

```bash
# Install ollama and pull the model
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen3.5:9b

# Clone and setup
git clone https://github.com/SohniSwatantra/autoresearch-local-llm.git
cd autoresearch-local-llm
pip install uv && uv sync

# Run
bash run_pipeline.sh
```

Requires 24GB+ VRAM (48GB recommended).

## Links

- Fork: [SohniSwatantra/autoresearch-local-llm](https://github.com/SohniSwatantra/autoresearch-local-llm)
- Original: [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
