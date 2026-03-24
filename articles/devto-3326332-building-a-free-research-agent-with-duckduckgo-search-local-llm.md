---
title: "Building a Free Research Agent with DuckDuckGo Search + Local LLM"
date: 2026-03-08
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/ddg-nemotron-research"
devto_url: "https://dev.to/soytuber/building-a-free-research-agent-with-duckduckgo-search-local-llm-5bjb"
devto_id: 3326332
---

## Why DuckDuckGo + Local LLM?

When conducting research, using paid APIs (such as Brave Search) is common, but by utilizing the ddgs library, you can perform web searches without an API key.

- Cost: It can be used completely free of charge (though with rate limits).
- Local LLM Integration: Search results can be passed to Nemotron (running on vLLM) to achieve highly accurate analysis with RAG.

Note that ddgs is an unofficial DuckDuckGo library, and search queries themselves are sent to DuckDuckGo's servers. Please be aware that this is not a completely local data processing solution.

## How to Use the ddgs Library

```bash
pip install duckduckgo-search
```

```python
from duckduckgo_search import DDGS

ddgs = DDGS()
results = ddgs.text("2026年 技術トレンド", region="jp-jp", max_results=5)
for result in results:
    print(f"Title: {result['title']}, URL: {result['href']}")
```

- Region Specification: `region="jp-jp"` prioritizes Japanese search results.
- News Search: You can retrieve news feeds using `ddgs.news("AI規制", region="jp-jp")`.
- DuckDuckGo does not officially recommend scraping, so excessive requests may be blocked.

## RAG Pipeline to Inject Search Results into Nemotron

```python
from duckduckgo_search import DDGS
from openai import OpenAI

# 1. Get search results with ddgs
ddgs = DDGS()
search_results = ddgs.text("最新GPUベンチマーク", region="jp-jp", max_results=3)
context = "\n".join([f"【{r['title']}】{r['body']}" for r in search_results])

# 2. Summarize with vLLM's OpenAI-compatible API
client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
response = client.chat.completions.create(
    model="nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese",
    messages=[
        {"role": "system", "content": "以下の検索結果を参考に回答してください"},
        {"role": "user", "content": f"{context}\n\n上記情報をもとに、最新技術トレンドを300字で要約してください。"}
    ]
)
print(response.choices[0].message.content)
```

## Comparison with Brave Search API

- ddgs (Free): No API key required, strong for Japanese searches, suitable for personal development and prototypes.
- Brave Search API (Paid): Official API, high throughput, suitable for large-scale enterprise analysis.

## Application to Batch Article Generation

The combination of ddgs + Nemotron also enables automated content generation based on search results. Following a search -> summary -> Markdown output flow, you can generate traceable articles with clearly stated source URLs.

## Summary

The combination of DuckDuckGo search + local LLM provides a free and achievable RAG pipeline. It enables privacy protection through local processing of search data (excluding search query transmission) and low-cost research automation.
