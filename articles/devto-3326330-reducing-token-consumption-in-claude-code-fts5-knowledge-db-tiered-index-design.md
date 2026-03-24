---
title: "Reducing Token Consumption in Claude Code — FTS5 Knowledge DB + Tiered Index Design"
date: 2026-03-08
topics: ["devtools", "python", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/claude-code-knowledge"
devto_url: "https://dev.to/soytuber/reducing-token-consumption-in-claude-code-fts5-knowledge-db-tiered-index-design-1eb4"
devto_id: 3326330
---

## Problem

If all coding conventions, test commands, and documentation for the entire project are written in CLAUDE.md, a large number of tokens will be consumed every turn. This can put pressure on the LLM's context window and lead to a decrease in quality.

## Solution: Two-Tier Structure

This design significantly reduces token consumption with a two-tier structure: "Tier 1 Index" and "Tier 2 FTS5 DB". Tier 1 is a lightweight index of less than 600 tokens, carefully selecting basic project rules and frequently used commands. Tier 2 provides an FTS5-based full-text search DB for deep-dive searches only when necessary.

## Extraction Pipeline

We have built a pipeline to automatically extract information from Claude Code execution logs. Code templates and prompt patterns are classified and accumulated using the following procedure.

```bash
python3 extract_templates.py --input session_log.jsonl --output templates.json
```

This script parses session logs and automatically extracts conventions, commands, and test scripts. It performs Japanese full-text search with FTS5 and removes duplicates.

## Classification by Local LLM

Nemotron is run locally to perform fast classification with `thinking OFF` and `max_tokens 64` settings. Extracted templates are quickly classified into "Required", "Optional", or "Not Applicable".

```python
response = nemotron_classify(
    input_text=template,
    max_tokens=64,
    thinking=False
)
```

## Tier 1 Selection with Gemini's Large Context

The classified templates are filtered by priority using Gemini's large context. Selection criteria are evaluated on two axes: "Execution Frequency (past 7 days)" and "Project Importance".

```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"以下のテンプレート一覧から重要度順にTier1を選別してください:\n{tier_list}"
)
```

Top templates are saved to `tier_1_index.json` and preferentially referenced during prompt generation for each turn.

## Cross-Session Memory with memory.db

Knowledge from multiple sessions is centrally managed using a memory DB (`memory.db`) leveraging FTS5.

```sql
SELECT * FROM rules WHERE rules MATCH 'テストコマンド';
```

## Benefits

- Significantly reduced token consumption per turn
- Efficiently search and provide only necessary information
- Selection pipeline combining Nemotron's local inference and Gemini's large context

## Summary

An architecture that efficiently manages basic rules with a Tier 1 index and performs deep-dive searches only when necessary using FTS5 is key to overcoming LLM context window constraints. The "selection → search" pipeline, combining Nemotron's local inference and Gemini's large context, can be immediately implemented in a personal development environment.
