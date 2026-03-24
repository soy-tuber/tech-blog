---
title: "I Posted My Patent Search AI to Reddit r/LocalLLaMA and Got 65 Upvotes and Over 20 Questions"
date: 2026-03-14
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/reddit-qa-patent-search"
devto_url: "https://dev.to/soytuber/i-posted-my-patent-search-ai-to-reddit-rlocalllama-and-got-65-upvotes-and-over-20-questions-5hbc"
devto_id: 3349947
---

## The Time I Posted a Patent Search Engine to Reddit r/LocalLLaMA and Received 65 Upvotes and Over 20 Technical Questions in 2 Hours

## Introduction

On the night of March 8, 2026, I posted my free custom patent search engine, patentllm.org (https://patentllm.org), to Reddit's r/LocalLLaMA (a local LLM community with 995,000 members).

The title was "I classified 3.5M US patents with Nemotron 9B on a single RTX 5090 — then built a free search engine on top".
reddit.com/r/LocalLLaMA/comments/1ro52cu/comment/o9bfwnh (https://www.reddit.com/r/LocalLLaMA/comments/1ro52cu/comment/o9bfwnh)

Two hours after posting, I got 65 upvotes and over 20 comments. Furthermore, the quality of those comments was exceptionally high. Below, based on actual exchanges, I record the questions I received from the international engineer community and the design philosophy drawn out from them.

## What I Posted

- Acquired 3.54 million US patent records from USPTO PatentsView
- Built an index with FTS5 in a 74GB SQLite file
- Classified all records into 100 tag categories using Nemotron-Nano-9B (no quantization) on an RTX 5090
- BM25 ranking (Title 10.0, Applicant 5.0, Abstract 3.0, Claims 1.0)
- Server-side rendering with FastAPI + Jinja2
- Delivered via Cloudflare Tunnel

## Q&A: Questions and Answers from International Engineers

### Q1: "Why FTS5 instead of vector search?"

This was the most frequently asked question. Since vector search is mainstream in r/LocalLLaMA, going against the grain stood out.

Summary of Answer: In patent searches, exact phrase matching is crucial. "solid-state battery electrolyte" and "energy storage medium" might be close in vector space, but under patent law, they are completely different. With FTS5, exact match searches, Boolean operations, and BM25 ranking are entirely handled within SQLite. Even with 3.5M records, it returns in sub-seconds.

Furthermore, for conceptual queries (natural language like "obstacle detection in autonomous driving"), I address them using LLM-based query expansion rather than vector search. The local LLM converts the input into queries for FTS5, but during this process, I restrict it to selecting search terms exclusively from a pre-extracted keyword index from the corpus. This prevents the LLM from "hallucinating" non-existent terms.

### Q2: "Why not make it a hybrid (Vector + FTS5)?"

Summary of Answer: I am considering it for the future. However, when I actually tried LanceDB, building an index for 3.5M records was unstable and got interrupted. SQLite proved to be more stable and predictable. Since LLM-based query expansion sufficiently covers my needs right now, I will maintain the current approach until I hit a performance wall.

### Q3: "How did you decide on the 100 tech tags?"

Two people asked the exact same question. It seemed to be an interesting technical point.

Summary of Answer: A two-stage approach. First, I had Gemini tag tens of thousands of patents in a free-form manner, aggregated the results, and organized them into meaningful top 100 categories. Next, I provided that fixed list to Nemotron-Nano-9B (no quantization, full precision) and had it classify all records. Currently, I have processed CPC sections G (Physics) and H (Electricity), which took about 30 hours on the RTX 5090.

### Q4: "Shouldn't you partition the 74GB SQLite file?"

A suggestion that I should split it by year and read it multi-threaded.

Summary of Answer: Currently, with a single 74GB file, FTS5 queries return in sub-seconds, so no issues have occurred. By design, I am assuming 1 DB per 10 years. The current DB covers 2016-2025, and I am building the 2005-2015 data as a separate file. By letting users select which era to search, I plan to handle differences in search frequencies and keep the DBs loosely coupled. Backups simply end with a `cp` command.

### Q5: "How are you deduplicating patent families?"

The issue where continuation applications and divisional applications result in a mass of similar patents in search results.

Summary of Answer: Honestly, I haven't done it yet. While the combination of BM25 + recency weighting (30%) tends to bring the latest family members to the top, it's not a fundamental solution. Because PatentsView data includes application reference information, it can be used for grouping families. It is on the roadmap.

### Q6: "Are there concerns about clients' confidential information leaking to the LLM?"

A sharp question touching on the confidentiality obligations of patent attorneys.

Summary of Answer: The free search (patentllm.org) is a zero-log design. Search histories are saved neither on the server nor on the client side. The DB connection is read-only. Since the search targets are entirely USPTO public data, the issue of confidential information does not arise. In the AI analysis layer, I use a local LLM (Nemotron on RTX 5090) designed so that data never leaves for a third-party server. This is the main reason I chose self-hosting over cloud APIs.

### Q7: "Can you add an AI summarization feature to each patent?"

Summary of Answer: I thought a bit about wrapping it with a lightweight model (like Gemini Flash Lite) to generate on-demand (a common technique), but I have yet to verify if the context window is sufficient.

### Q8 & 9: "Is there a prior art search feature?" "Will there be a paid version?"

Summary of Answer: The AI analysis layer (7 templates including prior art search, FTO analysis, and competitive landscape) is already built, but public release is at least half a year away. As a solo developer, beyond ensuring quality and stability, there are numerous cost and legal challenges (liability waivers, information management) that require careful consideration. The free search will continue to remain free.

## Memorable Comments

"patent lawyer who learned to code in December and processed 3.5M documents with a local model by March — this is the AI transition story in one post"

"74GB SQLite file on a Chromebook via tunnel is unhinged in the best way"

"What a time to be alive. When people talk about AI democratizing software engineering, and the era of personalized software, this is exactly the kind of stuff I think about."

"The 'vector search solves everything' crowd has never had to litigate over an exact phrase."

Looking at online communities, there are many "I succeeded in X" posts, but I felt there was still a weak culture of debating the judgments behind those technical selections. However, Reddit's r/LocalLLaMA is a place where "people actually running LLMs locally" gather, and I was impressed that practical dialogues like "Why did you choose that?" and "Here's how I do it" naturally arise among practitioners.

patentllm.org (https://patentllm.org) — Searches are free. No login. No logs.
