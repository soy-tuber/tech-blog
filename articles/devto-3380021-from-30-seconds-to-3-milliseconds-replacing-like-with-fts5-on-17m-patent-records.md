---
title: "From 30 Seconds to 3 Milliseconds: Replacing LIKE with FTS5 on 1.7M Patent Records"
date: 2026-03-21
topics: ["sqlite", "database", "performance", "search"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/nemotron-fts5-patent-speedup"
devto_url: "https://dev.to/soytuber/from-30-seconds-to-3-milliseconds-replacing-like-with-fts5-on-17m-patent-records-2bo7"
devto_id: 3380021
---


If you've ever written `WHERE column LIKE '%keyword%'` on a table with more than a million rows, you already know the pain. The query planner shrugs, does a full table scan, and you sit there watching a spinner for 10-30 seconds.

That was exactly my situation with [PatentLLM](https://patentllm.org) — a patent search engine built on SQLite with 1.73 million US patent records. Every search meant scanning every single row. No ranking. No stemming. No boolean operators. Just raw, brute-force string matching.

The fix was embarrassingly simple: SQLite's built-in FTS5 extension.

## The Three Fatal Flaws of LIKE

**1. Performance.** A `LIKE '%battery%'` query on 1.73M rows takes 10-30 seconds. That's not a search engine — that's a test of user patience.

**2. No ranking.** LIKE returns rows in insertion order. The most relevant result might be row 1,700,000. The user sees whatever happened to be inserted first.

**3. No boolean logic.** Want to search `battery OR lithium NOT sodium`? With LIKE, you're manually building `WHERE col LIKE '%battery%' OR col LIKE '%lithium%' AND col NOT LIKE '%sodium%'` — ugly, slow, and wrong (operator precedence will bite you).

## What FTS5 Actually Does

FTS5 (Full-Text Search version 5) is SQLite's built-in full-text search engine. It creates an **inverted index** — essentially a dictionary that maps every word to the list of rows containing it.

Think of it this way: LIKE reads every page of a book looking for a word. FTS5 flips to the index at the back of the book and looks up the page numbers directly.

Here's what you get out of the box:

- **Inverted index**: Look up "battery" and instantly get row IDs `[12, 345, 1089, ...]`
- **BM25 ranking**: Automatic relevance scoring based on term frequency and inverse document frequency — the same algorithm behind early search engines
- **Boolean operators**: `battery OR lithium NOT sodium` in a single query
- **Prefix queries**: `batt*` matches battery, batteries, batting
- **Phrase queries**: `"lithium ion battery"` matches only that exact sequence

## Implementation in 5 Minutes

The migration from LIKE to FTS5 is surprisingly painless:

```sql
-- Step 1: Create the FTS5 virtual table
CREATE VIRTUAL TABLE cases_fts USING fts5(
    title,
    abstract,
    claims,
    content='merged_cases',
    content_rowid='rowid'
);

-- Step 2: Populate the index (takes ~2 minutes for 1.73M rows)
INSERT INTO cases_fts(rowid, title, abstract, claims)
SELECT rowid, raw_case_name, summary, analysis_json
FROM merged_cases;
```

That's it. No external dependencies. No Elasticsearch cluster. No Docker containers. Just two SQL statements.

## Before and After

```sql
-- BEFORE: Full table scan, no ranking, 10-30 seconds
SELECT * FROM merged_cases
WHERE raw_case_name LIKE '%battery%'
   OR summary LIKE '%battery%';

-- AFTER: Index lookup, BM25 ranking, ~3 milliseconds
SELECT m.*, rank
FROM cases_fts f
JOIN merged_cases m ON f.rowid = m.rowid
WHERE cases_fts MATCH 'battery'
ORDER BY rank;
```

The performance difference isn't 2x or 5x. It's **100x to 10,000x** depending on the query. On my Chromebook (ARM64, 8GB RAM), complex boolean queries that used to timeout now complete in under 10 milliseconds.

## BM25: Why Ranking Matters More Than Speed

Honestly, the ranking improvement mattered more than the speed improvement. With LIKE, if you search for "machine learning patent classification," you get results in random order. With FTS5's BM25 ranking, documents that contain all three terms — especially in their title or abstract — float to the top.

BM25 is deceptively simple:

- Documents where the search term appears frequently rank higher (term frequency)
- But terms that appear in many documents are worth less (inverse document frequency)
- Shorter documents get a slight boost (they're more focused)

This is the same core algorithm Google used in its early days, and for a corpus like patent abstracts, it works remarkably well.

## Gotchas I Discovered

**1. FTS5 OR syntax uses implicit OR by default.** If you write `MATCH 'battery lithium'`, FTS5 treats this as `battery AND lithium`. For OR, you must be explicit: `MATCH 'battery OR lithium'`.

**2. Content sync.** If you use `content=` to create an external-content FTS table, remember that FTS5 doesn't auto-sync. When you INSERT/UPDATE/DELETE the main table, you need to update the FTS index separately (or use triggers).

**3. Index size.** The FTS5 index added about 40% to my database size (from ~8GB to ~11GB). For most use cases this is fine, but be aware if you're tight on disk.

**4. Porter stemmer.** Adding `tokenize='porter unicode61'` enables English stemming — "batteries" and "battery" will match. This is almost always what you want for English text, but test it with your specific corpus first.

## When NOT to Use FTS5

FTS5 isn't always the answer:

- **Exact substring matching**: FTS5 is word-based. If you need to find "batt" inside "battery," you need `LIKE '%batt%'` or FTS5's prefix query `batt*`
- **Regex patterns**: FTS5 doesn't support regular expressions
- **Non-text data**: If you're searching numeric ranges or dates, use regular indexes
- **Real-time indexing at massive scale**: FTS5 handles millions of rows fine for batch inserts, but if you're doing thousands of inserts per second, you might want to batch your index updates

For everything else — especially if you're already using SQLite — FTS5 is free performance sitting right there in your database.

## The Bottom Line

If you have a SQLite database with more than 100K text rows and you're using LIKE for search, stop what you're doing and add FTS5. It's two SQL statements, zero dependencies, and the difference between "this app feels broken" and "this app feels instant."

The 1.73 million patent records in PatentLLM now search in 3 milliseconds. The only regret is not doing it on day one.


*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090.*

