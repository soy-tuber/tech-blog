---
title: "What I Gained from Interacting with Shogi AI: The Path to 1st Place in Floodgate and My Approach to Distilled Models"
date: 2026-03-14
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/mega-shogi-ai"
devto_url: "https://dev.to/soytuber/what-i-gained-from-interacting-with-shogi-ai-the-path-to-1st-place-in-floodgate-and-my-approach-to-4k63"
devto_id: 3349941
---

## Introduction

As a practical testing ground for verifying reasoning optimization and model handling, I first touched an OSS shogi software in January 2026.

As a result, I reached rank 1 by playing over 200 games with a rating exceeding 4500 on Floodgate (an online shogi server for computer shogi). Since I started programming in December 2025, this was achieved in approximately two months after touching the OSS.

This article is not a how-to guide on implementation, but rather discusses what was learned through shogi AI and how it can be applied to LLM research from the perspective of an LLM/RAG researcher.

## Why Chess AI?

In LLM research, one frequently encounters challenges such as reasoning optimization and model selection. However, LLM evaluation can be ambiguous. "Is the answer good?" often involves subjectivity. In contrast, shogi AI has clear wins/losses and ratings, allowing immediate numerical verification of strategy effectiveness.

Additionally, skill sets such as CUDA/TensorRT build and batch processing optimization are completely common between LLM and shogi AI. Shogi AI serves as an ideal experimental ground for verifying these technologies through a strict win/loss feedback loop.

## Overall Architecture: 3-Layer Hybrid

The constructed system has a 3-layer architecture.

Phase 1: Book (Opening Database) — Immediate move via Python dictionary lookup. No C++ engine startup, zero GPU/CPU load.
Phase 2: MCTS + DL Model — Inference of a large 40-block ResNet using TensorRT. Quantized to fit within RTX 5090's 32GB VRAM.
Phase 3: α-β + NNUE — Fast position evaluation via CPU search. Handles endgame reading victories.

A Python wrapper manages phase switching and protocol communication, selecting engines based on position characteristics. This design philosophy of "winning with the entire architecture rather than a single model" is fundamentally the same as RAG system composition (search → ranking → generation multi-stage pipeline).

## OSS Modification: The Value of Cutting

I forked two OSS engines (DL and NNUE) and removed unnecessary features at the source level.

In the DL engine, features such as multi-GPU support, multiple backend branching, and various mate search were removed to specialize for RTX 5090 × TensorRT. USI options were reduced from 63 to 43 (-32%).

In the NNUE engine, test commands, book generation commands, and learning-related code were compiled out, reducing binary size from 916KB to 514KB (44% reduction).

This "cutting" work directly applies to LLM operations. Instead of adding functionality via LoRA or Fine-Tuning to distilled models, reduce unnecessary branches and control via prompts — a policy fully aligned with the article "An Era Without LoRA or FT: How to Approach Distilled Models."

## Real-Time Book Rewriting: RAG-Inspired Approach

We manage a database of approximately 7 million book positions on the Python side. Book loading has been accelerated.

A notable feature is the real-time rewriting of the book during matches. After a loss, the early-game branching points are identified, and the book is modified to select different moves in the next match. The book is continuously refined as matches accumulate.

This "updating the database from experience and reflecting it in subsequent reasoning" cycle is identical to the feedback loop in RAG. The structure is the same as improving search result quality from dialogue logs.

## LLM Utilization and Limitations

During development, I used Claude Opus as a coding partner. For niche specialized tools like dlshogi and YaneuraOu, LLM hallucinations frequently occur. Blindly trusting confidently generated code can lead to incorrect modifications that not only don't work but also lower shogi strength.

The lesson here is that "LLM is translation, not reasoning." The correct usage is to perform calculations with specialized engines (e.g., search engines for shogi AI, domain-specific logic for business) and use LLM for natural language translation of inputs/outputs. This aligns with RAG design principles: "Don't give LLM knowledge, but generate based on facts obtained from external sources."

## Conclusion: Research is Cyclical

After organizing insights from two months of shogi AI development:

- Additional learning on distilled models is ineffective or leads to overfitting → Prompt control is the correct approach
- Winning with the entire architecture, not a single model → RAG pipeline design philosophy
- Updating the database from experience and reflecting it in subsequent reasoning → RAG feedback loop
- LLM is translation, not reasoning → Domain logic should be handled by specialized engines

This shogi AI experience has been returned to LLM research, and LLM research insights have been applied to shogi AI architecture design. This cycle is the greatest value of venturing into different fields. Currently, I'm back to researching local LLMs (building systems using NVIDIA's Nemotron models), but I'll participate again when the GPU is free. It was very enjoyable.

Hardware Used:
- GPU: NVIDIA RTX 5090 (32GB GDDR7)
- CPU: Intel Core Ultra 9 285K
- RAM: 64GB
- OS: Linux (WSL2)
