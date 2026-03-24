---
title: "When Gemini Hallucinates Patent Numbers: Fixing the FTS5 + LLM Analysis Pipeline"
date: 2026-03-21
topics: ["ai", "sqlite", "search", "llm"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-fts5-gemini-pipeline"
devto_url: "https://dev.to/soytuber/when-gemini-hallucinates-patent-numbers-fixing-the-fts5-llm-analysis-pipeline-173o"
devto_id: 3380011
---


I built a patent analysis pipeline that combines SQLite FTS5 search with Gemini's analytical capabilities. The idea: give Gemini a research hypothesis, let it generate search keywords, query 3.5 million patents via FTS5, then have Gemini analyze the actual results.

In theory, this marries the precision of database search with the analytical power of an LLM. In practice, every hypothesis returned zero database hits, and Gemini — being helpful — started inventing patent numbers.

## The Architecture

The pipeline has three stages:

1. **Hypothesis generation**: Gemini receives a research topic and generates specific hypotheses with suggested search keywords
2. **Database search**: The keywords are used in FTS5 MATCH queries against the patent database
3. **Analysis**: Gemini receives the actual patent records and generates an analysis report

The script `run_prior_art_search.py` orchestrated this flow. The problem was in stage 2 — every search returned zero results.

## Root Cause: Gemini Writes Terrible FTS5 Queries

Gemini generated keywords like this:

```plaintext
"retrieval AND augmented AND generation"
```

This looks reasonable in English, but it's catastrophically wrong as an FTS5 query. Here's why:

**FTS5 treats quoted strings as phrase queries.** So `"retrieval AND augmented AND generation"` searches for the literal phrase "retrieval AND augmented AND generation" — including the words "AND" — which obviously doesn't appear in any patent.

Without quotes, `retrieval AND augmented AND generation` requires all three terms to appear in the same document, which is more reasonable. But Gemini also generated overly specific compound phrases like `"patent portfolio comparison similarity analysis"` — five-word phrases that never appear verbatim in any document.

On the other end, generic single keywords like `patent` matched 1.64 million out of 3.5 million records.

## The Zero-Result Hallucination Problem

When the database returned zero results, Gemini didn't say "no results found." Instead, it did what LLMs do — it generated plausible-looking patent numbers:

```plaintext
[Inference] US-2021/0234567 - "System for Retrieval-Augmented Generation..."
[Inference] US-2022/0891234 - "Neural Network-Based Patent Analysis..."
```

The `[Inference]` tag was technically honest, but a downstream consumer of this report would see patent numbers and assume they were real. This is a concrete example of why LLM-generated content needs ground truth validation.

## The Three Fixes

### Fix 1: Manual FTS5 Keywords Override

Instead of trusting Gemini to generate syntactically correct FTS5 queries, I added a manual keyword override:

```python
# Before: Gemini generates everything
query = analyze_query(hypothesis)  # Broken FTS5 syntax

# After: Manual keywords take priority
if 'fts_keywords' in hypotheses[hypothesis]:
    query = hypotheses[hypothesis]['fts_keywords']
else:
    query = analyze_query(hypothesis)
```

The manual keywords use proper FTS5 syntax: `"retrieval augmented" OR "RAG" OR "retrieval-augmented"`.

### Fix 2: FTS5 OR Syntax

This was the subtlest bug. In FTS5, `OR` must be uppercase and used as an infix operator:

```sql
-- WRONG: Parentheses may cause issues without proper grouping
"patent portfolio" AND (comparison OR similarity)

-- CORRECT: Explicit grouping with proper syntax
("patent portfolio") AND (comparison OR similarity)
```

The parentheses around OR groups are important. Without them, FTS5's operator precedence can produce unexpected results.

### Fix 3: Hit Count Validation

Before sending results to Gemini, the pipeline now validates that the hit count is within a useful range:

```python
count = db.execute(
    "SELECT COUNT(*) FROM cases_fts WHERE cases_fts MATCH ?",
    (query,)
).fetchone()[0]

if count == 0:
    query = broaden_query(query)  # Remove least important term
elif count > 100:
    query = narrow_query(query)   # Add specificity
```

The target range is 10-30 results — enough for meaningful analysis, few enough that Gemini can read all of them.

## Results After Fixing

| Hypothesis | Before (hits) | After (hits) |
|-----------|--------------|-------------|
| RAG in patent search | 0 | 51 |
| Portfolio comparison | 0 | 12 |
| ML classification | 0 | 23 |
| NLP for claims | 0 | 39 |

The analysis reports went from fabricated patent numbers to actual, verifiable citations with real patent text. The quality difference was night and day.

## The Bigger Lesson: LLMs Need Guardrails for Structured Queries

This experience crystallized something important: **LLMs are unreliable at generating syntactically precise queries for specific query languages.** SQL, FTS5, Elasticsearch DSL, regex — the LLM understands the *intent* but frequently gets the *syntax* wrong.

The pattern that works:

1. Let the LLM generate *concepts* and *intent* (natural language)
2. Use deterministic code to translate intent into syntactically correct queries
3. Validate results before passing them back to the LLM
4. Never let the LLM fill gaps with hallucinated data — fail explicitly instead

This isn't a limitation of Gemini specifically. I've seen the same pattern with Claude, GPT-4, and local models. The fix is always the same: don't let the LLM touch the query syntax directly.


*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090.*

