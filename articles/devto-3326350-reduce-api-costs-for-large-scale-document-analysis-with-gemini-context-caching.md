---
title: "Reduce API Costs for Large-Scale Document Analysis with Gemini Context Caching"
date: 2026-03-08
topics: ["ai", "machinelearning", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/gemini-context-cache"
devto_url: "https://dev.to/soytuber/reduce-api-costs-for-large-scale-document-analysis-with-gemini-context-caching-31kn"
devto_id: 3326350
---

## What is Context Caching?

Google Gemini's Context Caching is a feature that caches context once it's input and reuses it in subsequent requests. Cached tokens can be used at approximately 25% of the standard rate, enabling significant cost savings.

### Basic Specifications

- Cache Validity Period: Default 3,600 seconds (1 hour)
- Token Requirement: Minimum 32,768 tokens
- Model-Specific Isolation: Caches are managed in conjunction with the model name.

## Use Cases

### Large-Scale DB Analysis

When analyzing an SQLite DB built with FTS5+BM25, leveraging Context Caching can be highly effective.

- Keyword Extraction Phase: Fast processing with the Flash model
- Answer Generation Phase: High-accuracy analysis with the Pro model
- Fact-Checking Phase: Cache training data to reduce processing time

### Batch Analysis

During batch processing, reusing the same context across all samples is effective.

```bash
from google import genai
from google.genai import caching

client = genai.Client()

# キャッシュ作成（32,768トークン以上が必要）
cached_content = caching.CachedContent.create(
    client=client,
    name="patent_batch_cache",
    contents=[{"text": doc["title"]} for doc in patent_docs[:1000]],
    model="gemini-2.5-flash",
    config={"expire_time": "2026-03-09T00:00:00Z"}
)

# キャッシュを使った生成
for doc in patent_docs:
    result = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=doc["text"],
        cached_content=cached_content.name
    )
```

## Cost Calculation Example

For training data of 75,458 tokens:
- Without caching: Standard rate
- With caching: Approximately 25% of the standard rate

When the same context is repeatedly used in batch processing, the effect of caching becomes very significant.

## Limitations and Considerations

- A minimum of 32,768 tokens is required when creating a cache.
- Caches are isolated per model, so sharing caches between different models is not possible.
- It is important to set the expiration time to match the analysis processing time.

## Summary

By appropriately utilizing Context Caching, you can significantly reduce API costs for large-scale data analysis and shorten processing times. The key to success is to use the Flash model for keyword extraction, the Pro model for answer generation, and to reuse the same context during batch processing.
