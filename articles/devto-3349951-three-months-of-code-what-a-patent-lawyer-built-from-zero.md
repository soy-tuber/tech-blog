---
title: "Three Months of Code: What a Patent Lawyer Built from Zero"
date: 2026-03-14
topics: ["programming", "career", "beginners"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/other/three-months-of-code"
devto_url: "https://dev.to/soytuber/three-months-of-code-what-a-patent-lawyer-built-from-zero-3dnp"
devto_id: 3349951
---

I built a multi-engine shogi AI, deployed it to rated games on Floodgate, and watched it lose to programs it should have crushed.

I'm a patent lawyer. I'd been writing code for less than two months when that happened. Three months ago, in December 2025, I wrote my first line of code. This is the record of what I built, what broke, and what I learned by deleting most of it.

## The Failure That Taught Me Everything

I designed a multi-engine consultation architecture — the kind of thing that sounds impressive on paper. Multiple engines voting on the best move, weighted evaluation, the works. I deployed it to rated games, and it got weaker.

The obvious reaction would have been to tune parameters. Instead, I traced the actual cause. Engine R2 was running with multipv=3, generating its top three candidate moves. Those alternative moves were bleeding into the primary engine's evaluation as noise. The consultation wasn't adding signal — it was adding confusion.

The correct answer was deletion. Remove the consultation. Remove the noise. Let the strongest single engine think without interference. Suisho 11 alone, uncontaminated, was the strongest configuration.

This is a pattern I kept encountering. The instinct to add complexity is almost always wrong. The instinct to remove it is almost always right.

After removing everything unnecessary, the shogi AI reached Rating 4500 and held the #1 position on Floodgate for two weeks. 40-block ResNet, FP8 inference, 1,750 TensorRT build attempts, and roughly 50% of the dlshogi/YaneuraOu codebase deleted. The strongest configuration was the simplest one.

## What I Built

**PatentLLM** — A search engine covering 3.54 million US patents (2016–2025). SQLite FTS5 full-text search, BM25 ranking, 100-category automatic classification using Nemotron 9B with 94% accuracy.

**HanreiLLM** — A Japanese case law database with keyword-constrained RAG. The approach is described in the next section.

**Nemotron Pipeline** — A Flutter PWA with 6 features, plus a batch processing pipeline handling 1.74 million records in BF16 precision. I refused quantization throughout.

Also built: GEO monitoring (Gemini Flash-Lite + Brave Search), stock analysis tracking (Serper.dev), automated blog translation pipeline (Dev.to/Hashnode), and production infrastructure on a Chromebook with Cloudflare Tunnel, Tailscale SSH, and FastAPI audit logging.

## The RAG System

Building the case law search taught me the same lesson from a different angle. I evaluated LanceDB for vector search and decided it was unnecessary. I considered letting the LLM generate search keywords dynamically and realized it was unreliable.

The solution I landed on: pre-index a keyword dictionary directly into the SQLite database, then use that dictionary to constrain the LLM's output. The model doesn't get to hallucinate keywords. It picks from a verified set, and the database returns exact matches.

This is the kind of architecture that feels obvious in retrospect but requires discarding the assumption that more sophisticated technology produces better results.

## Technology Decisions as Subtraction

My technology choices were defined more by what I rejected than what I adopted:

- **LoRA fine-tuning** — Evaluated, rejected. The base model was sufficient.
- **Unsloth** — Evaluated, rejected. Unnecessary optimization layer.
- **Quantization** — Refused entirely. BF16 or nothing. The precision loss wasn't worth the VRAM savings.
- **Multi-engine consultation** — Built, deployed, measured, removed. Noise disguised as signal.
- **Dynamic keyword generation** — Prototyped, abandoned. Pre-indexing was more reliable.
- **Time-based tier management** — Implemented, found harmful, deleted.

Each rejection was based on measurement, not assumption. I built the thing, tested it under real conditions, and removed it when the data showed it was harmful or unnecessary.

## Why Three Months Was Enough

I don't think coding speed explains this. What explains it is the transferable structure of legal training.

**Separating fact from inference.** Patent law trains you to distinguish what the evidence actually shows from what you wish it showed. When the shogi AI got weaker, I didn't generate theories — I traced the causal chain until I found the specific variable responsible. This is the same cognitive operation as interpreting a patent claim against prior art.

**The speed of "no."** Experienced patent practitioners spend most of their time deciding what *not* to claim. Narrowing scope is the skill. The same instinct drove every technology rejection above. Beginners want to add capabilities. Practitioners want to remove liability.

**Using tools correctly.** I used Claude Code extensively, but I also identified when it was producing tangled, over-engineered output and intervened. The boundary between "delegate to AI" and "decide myself" was never ambiguous to me, because managing the boundary between "delegate to associate" and "decide myself" is what senior lawyers do every day.

**Domain knowledge as architecture.** Attorney-client privilege mapped directly to zero-log system design. Evidence chain-of-custody mapped to audit logging. Claim construction mapped to API design. The abstractions were the same; only the implementation language changed.

## The Chromebook as Production Server

One choice that surprises people: my production server is a Chromebook. ARM64, Debian bookworm running in Crostini. It handles all non-GPU workloads — web serving, database queries, API routing, blog publishing.

GPU inference runs on a separate desktop with an RTX 5090, connected via Tailscale. The Chromebook calls the desktop when it needs model inference and handles everything else locally.

This architecture emerged from constraints, not theory. I had a Chromebook and a desktop. Instead of buying a server, I made what I had work. The Chromebook draws minimal power, runs 24/7 silently, and has proven entirely stable as a production host.

## What I Learned About Learning

Three months is not a long time. But I didn't spend those three months learning to code. I spent them applying twenty years of structured problem-solving to a new domain that happened to use a text editor instead of a legal brief.

The code is a side effect. The actual skill is the ability to look at a complex system, identify what matters, and remove everything else.

That skill doesn't come from programming tutorials. It comes from years of reading patent specifications and asking: *What is actually claimed here? What is the minimum viable scope? What can I delete without losing the invention?*

Every system I built followed the same process:
1. Define the problem precisely.
2. Build the simplest thing that could work.
3. Test it under real conditions.
4. Measure what's actually happening versus what I expected.
5. Remove everything that isn't contributing.

This is claim drafting. This is prior art analysis. This is patent prosecution. The vocabulary changed. The thinking didn't.

## Current State (March 2026)

Everything described above is running in production. The patent search engine serves real queries. The shogi AI plays rated games. The blog publishes automatically. The infrastructure has been stable for months.

I'm still a patent lawyer. I just also write code now.

The gap between "beginner" and "effective" is not about years of experience. It's about the quality of the mental models you bring to the problem. Legal training gave me models that transferred directly — and the discipline to delete everything that doesn't survive contact with reality.
