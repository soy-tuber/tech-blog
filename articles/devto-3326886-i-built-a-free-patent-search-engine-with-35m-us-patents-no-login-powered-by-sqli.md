---
title: "I Built a Free Patent Search Engine with 3.5M US Patents — No Login, Powered by SQLite FTS5"
date: 2026-03-08
topics: ["sqlite", "python", "llm", "showdev"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/patent-search-launch"
devto_url: "https://dev.to/soytuber/i-built-a-free-patent-search-engine-with-35m-us-patents-no-login-powered-by-sqlite-fts5-48e4"
devto_id: 3326886
---

I'm a patent lawyer who started coding in December 2025. Today I'm launching a free patent search engine covering 3.5 million US patents (2016–2025).

**Try it here: [patentllm.org](https://patentllm.org)**

No login. No ads. No API keys.

## Why I built this

Existing patent search tools fall into two camps:

- **Google Patents** — simple but no filtering, no relevance tuning
- **Commercial tools** (PatSnap, Derwent) — powerful but $10K+/year

I wanted something in between. Fast full-text search across titles, abstracts, and claims — with CPC classification filtering and smart relevance ranking — for free.

## The tech stack (intentionally boring)

| Component | Choice | Why |
|-----------|--------|-----|
| Database | SQLite (74GB, single file) | Zero ops. No Postgres. No containers. |
| Full-text search | FTS5 + BM25 | Built into SQLite. Handles 3.5M records without breaking a sweat. |
| Ranking | 70% BM25 + 30% recency | Newer patents get a boost. Patent relevance isn't just keyword matching. |
| Web framework | FastAPI + Jinja2 | Server-side rendering for SEO. Every search result has a unique URL. |
| LLM (tagging) | Nemotron 9B on RTX 5090 | Classified all 3.5M patents into 100 tech tags. Locally, zero API cost. |
| Hosting | Chromebook + Cloudflare Tunnel | Yes, really. |

## Why FTS5 instead of vector search?

Everyone's doing vector search with embeddings these days. I went the opposite direction.

For patent search, **exact phrase matching matters**. When a patent attorney searches for "solid-state battery electrolyte," they need documents containing those exact terms — not semantically similar documents about "energy storage solutions."

FTS5 gives me:
- Exact phrase matching with quotes
- Boolean operators (AND, OR, NOT)
- BM25 relevance scoring out of the box
- Sub-second queries on 3.5M records
- Zero external dependencies

I added a local LLM (Nemotron 9B) on top for **query expansion** — it converts natural language like "self-driving car obstacle detection" into FTS5 queries like `"autonomous driving" AND "obstacle detection"`. Best of both worlds.

## BM25 weight tuning

Default BM25 weights treat all fields equally. That doesn't work for patents. I tuned the weights based on how patent attorneys actually search:

- **Title: 10.0** — if your keyword is in the title, it's almost certainly relevant
- **Assignee: 5.0** — searching by company name should rank those patents highest
- **Abstract: 3.0** — the abstract is the patent's elevator pitch
- **Claims: 1.0** — claims are legally important but verbose; lower weight prevents noise

This produces results that match how an experienced patent searcher would rank them manually.

## The data pipeline

All data comes from [USPTO PatentsView](https://patentsview.org/) (public domain, Creative Commons):

1. Download bulk TSV files (titles, abstracts, claims, CPC classifications)
2. Parse and merge into SQLite
3. Build FTS5 virtual table across title + abstract + claims
4. Run Nemotron 9B over all 3.5M records for tech tag classification (took ~48 hours on RTX 5090)
5. Serve via FastAPI

The entire database is a single 74GB SQLite file. Backup is `cp`. Migration is `scp`.

## What you can do with it

- **Keyword search** across 3.5M patents with BM25 ranking
- **Filter by CPC section** (Physics, Electricity, Chemistry, etc.) with group drill-down
- **Filter by assignee** (Apple, Samsung, etc.)
- **Filter by date range**
- **View patent details** — abstract, claims, tech tags, CPC classification
- **Link to Google Patents** for full text and legal status

## What's next

I'm building an AI analysis layer on top (prior art search, FTO analysis, competitive landscape) — that will be the paid tier at [ai.patentllm.org](https://ai.patentllm.org).

The search will stay free forever.

## Feedback welcome

I'd love to hear from:
- Patent attorneys / IP professionals — does the ranking feel right?
- Engineers interested in patent data — what features would you want?
- Anyone who's built search at scale with SQLite — tips welcome

**[patentllm.org](https://patentllm.org)** — give it a try and let me know what you think.
