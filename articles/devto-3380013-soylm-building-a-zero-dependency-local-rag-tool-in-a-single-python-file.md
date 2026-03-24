---
title: "SoyLM: Building a Zero-Dependency Local RAG Tool in a Single Python File"
date: 2026-03-21
topics: ["python", "ai", "rag", "opensource"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-soylm-rag"
devto_url: "https://dev.to/soytuber/soylm-building-a-zero-dependency-local-rag-tool-in-a-single-python-file-5hee"
devto_id: 3380013
---


SoyLM started as a simple idea: build a RAG (Retrieval-Augmented Generation) tool that runs entirely on your machine. No cloud APIs. No vector databases. No Docker containers. Just one Python file.

Then someone pointed out that my README said "NotebookLM compatible" when it had nothing to do with NotebookLM. Which led to a documentation rewrite. Which led to removing Gemini API dependencies I'd forgotten about. Which led to rethinking the entire project identity.

Building the tool took a weekend. Figuring out what it actually *is* took much longer.

## What SoyLM Actually Does

SoyLM lets you upload documents (PDFs, text files, URLs, YouTube videos), then have a conversation about them with a local LLM. Behind the scenes:

1. **Source ingestion**: Documents are chunked, indexed in SQLite FTS5, and pre-analyzed by the LLM
2. **Query processing**: Your question triggers BM25 search to find relevant chunks
3. **Response generation**: The LLM receives your question + relevant chunks and generates a grounded response

The entire thing is a single `app.py` file using FastAPI with inline HTML/JS — no frontend build step, no node_modules, no React.

## The Architecture: Aggressively Simple

```plaintext
User -> FastAPI (app.py) -> SQLite FTS5 (search) -> Local LLM (vLLM) -> SSE response
```

Every component choice was driven by minimizing dependencies:

| Component | Choice | Why Not The Alternative |
|-----------|--------|----------------------|
| Search | SQLite FTS5 + BM25 | No vector DB setup, no embedding model needed |
| Backend | FastAPI | Async, built-in SSE support, one pip install |
| Frontend | Inline HTML/JS | No build step, no npm, no node_modules |
| LLM | vLLM (OpenAI-compatible) | Any model, any provider, same API |
| Storage | SQLite (single file) | No Postgres, no Redis, no Docker |

The total dependency list: `fastapi`, `uvicorn`, `sqlite3` (stdlib), `httpx`, and optionally `playwright` for YouTube transcription.

## The Pre-Analysis Trick

Most RAG tools analyze documents at query time — you ask a question, the system retrieves chunks, then the LLM reads them. This works but it's slow, especially with a local LLM.

SoyLM flips this: when you upload a document, the LLM immediately generates a summary and key topics. These pre-computed analyses are stored alongside the raw chunks. At query time, the search can match against both the original text and the LLM's analysis, improving recall without adding latency.

```python
async def flash_load_source(source_id: str):
    """Pre-analyze source on upload, not on query."""
    chunks = get_chunks(source_id)
    for chunk in chunks:
        analysis = await call_llm(
            f"Summarize the key topics in this text:\n{chunk.text}"
        )
        store_analysis(source_id, chunk.id, analysis)
```

This trades upload time (a few seconds per document) for query time (sub-second responses even with a local LLM).

## The NotebookLM Confusion

The original README opened with "SoyLM — a NotebookLM-compatible local RAG tool." This was wrong in multiple ways:

1. SoyLM has no connection to Google's NotebookLM
2. It doesn't use the same API or format
3. The name "SoyLM" has nothing to do with NotebookLM

How did this happen? The project started as an attempt to build something *like* NotebookLM but local. Somewhere in the writing process, "inspired by" became "compatible with." A subtle but important distinction that confused early users.

The fix was more than just changing a sentence. It required asking: what *is* SoyLM's identity?

**The answer: SoyLM = "Soy" (simple/plain) + "LM" (Language Model).** It's a local-first RAG tool for people who want to talk to their documents without sending anything to the cloud. The name itself signals simplicity.

## Removing the Gemini Ghost

While rewriting the README, I discovered that the codebase still had Gemini API references:

- An environment variable for `GEMINI_API_KEY`
- A model selection dropdown that included Gemini models
- A fallback that tried Gemini if the local LLM was unavailable

All of these contradicted the "local-first, no cloud" philosophy. I removed them entirely and hardcoded Nemotron 9B as the default model (configurable via environment variable to any OpenAI-compatible endpoint).

This was psychologically harder than it should have been. The Gemini fallback felt like a safety net — "what if the local model is down?" But a local-first tool with a cloud fallback is just a cloud tool with extra steps. Committing to local-only forced better error handling and a clearer user experience.

## YouTube Support via Playwright

One feature that users actually loved: paste a YouTube URL, and SoyLM transcribes it and adds it as a source. The implementation uses Playwright to load the YouTube page and extract the auto-generated transcript:

```python
async def get_youtube_transcript(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.click('[aria-label="Show transcript"]')
        transcript = await page.inner_text('.ytd-transcript-segment-renderer')
        await browser.close()
        return transcript
```

This is fragile — YouTube changes their DOM regularly — but it works surprisingly well for English content. A `yt-dlp` based fallback handles cases where Playwright fails.

## Posting to Reddit: The Real Test

I posted SoyLM to r/LocalLlama, which is the most discerning audience for local LLM tools. The response was a reality check:

**What people liked:**
- Single-file design (easy to audit, easy to understand)
- No vector database requirement
- YouTube support
- SQLite FTS5 instead of embeddings

**What people questioned:**
- "Why BM25 instead of embeddings?" (Answer: BM25 is simpler, requires no embedding model, and works well enough for document-level RAG)
- "Why not just use LangChain?" (Answer: LangChain adds massive complexity for something that can be 500 lines of Python)
- "Will this scale?" (Answer: it's designed for personal use with 10-100 documents, not enterprise scale)

The most valuable feedback was about positioning: SoyLM isn't trying to compete with LangChain or LlamaIndex. It's the "SQLite of RAG" — good enough for personal use, simple enough to understand completely, and local enough to trust with private documents.

## What I Learned

**README-driven development is real.** The act of rewriting the README forced me to clarify what the project is and isn't. Remove the Gemini fallback? That decision came from writing the sentence "SoyLM runs entirely on your machine" and realizing the code didn't match.

**FTS5 is underrated for RAG.** Everyone reaches for vector search, but BM25 keyword matching is surprisingly effective for document QA. You don't need semantic similarity when the user is asking "what does section 3.2 say about liability?" — that's a keyword match.

**Single-file projects have a maximum comfortable size.** SoyLM's `app.py` is about 800 lines. Above 1,000, single-file starts hurting readability. I'd split at that point, but not before.


*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090.*

