---
title: "How Google Finds Every Restaurant in Japan — And Why Your Full-Text Search Can't"
date: 2026-03-20
topics: ["search", "google", "sqlite", "architecture"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/ai/google-places-unagi-search"
devto_url: "https://dev.to/soytuber/how-google-finds-every-restaurant-in-japan-and-why-your-full-text-search-cant-3hmc"
devto_id: 3377720
---

I recently scraped every unagi (eel) restaurant in Japan using the Google Places Text Search API. The results were absurdly precise: **1,914 restaurants** across all 47 prefectures, with a noise rate under **1.6%**. No ML pipeline. No fine-tuned classifier. Just API calls.

Here's how that's possible — and what it reveals about the gap between "search" as most developers implement it and search as Google does it.

## The Task

I wanted a comprehensive database of unagi specialty restaurants in Japan. The naive approach: query `"うなぎ 鰻 {prefecture}"` for each of the 47 prefectures and collect the results.

That's exactly what I did. One query per prefecture. Save to JSONL. Done.

## The Surprising Precision

When I audited the results, here's what I found:

| Category | Count |
|---|---|
| Restaurant name contains eel-related terms (うなぎ, 鰻, うな, etc.) | 1,322 |
| Name doesn't match, but reviews mention eel | 562 |
| Potential noise (no eel reference anywhere) | 30 (1.6%) |

And even among those 30 "noise" candidates, most were legitimate eel restaurants with variant spellings — places like うな竹, うな真, 宇な義 — that my string-matching regex simply missed.

The true noise was **single digits**.

## Why FTS5 + BM25 Can't Do This

If you're a developer who's built search with SQLite FTS5 or Elasticsearch BM25, you know the limits. BM25 scores documents based on term frequency, inverse document frequency, and document length. It's elegant. It's fast. And it would fail miserably at this task.

Here's why: BM25 gives a score of **zero** to any document that doesn't contain your query terms. A restaurant called "川魚料理 山田" (River Fish Cuisine Yamada) that serves legendary eel but never uses the word うなぎ in its listing? Invisible to BM25.

Google's Text Search doesn't have this problem.

## What Google Actually Does (Beyond Vector Search)

When people hear "semantic search," they immediately think "vector embeddings." And yes, Google almost certainly uses vector representations — encoding "鰻," "うなぎ," "うな重," and "蒲焼" as nearby points in a high-dimensional space so they match semantically, not just lexically.

But vector search alone is a blunt instrument. Search `"うなぎ"` with pure vector similarity and you'll get あなご (conger eel) restaurants too, because the embeddings are close. You might even get seafood restaurants in general.

Google suppresses this noise by layering multiple signals:

**1. Structured Data from Google Business Profiles**
Restaurant owners register their own businesses, including cuisine type, menu items, and categories. This is authoritative, first-party data — not inferred.

**2. Knowledge Graph Relationships**
Google knows that うなぎ → eel → a specific cuisine category → associated with Japanese restaurants. These aren't just word associations; they're ontological relationships.

**3. Review Analysis at Scale**
When 50 reviewers independently write "the unaju here is the best in the prefecture," Google extracts and structures that signal. Individual reviews are noisy. The aggregate is remarkably clean.

**4. User Behavior Data**
People who search for "うなぎ 浜松" and then navigate to, call, or visit a specific restaurant are providing implicit ground truth. This click-through and visit data is unavailable to any open-source search system.

**5. Geographic Intelligence**
Restaurant density, regional cuisine patterns, and proximity all feed the ranking. A query for "うなぎ 浜松" weights Hamamatsu-area results differently than a generic nationwide search.

## The Architecture You'd Need to Replicate This

If you wanted to build this yourself without Google's API, you'd need:

- A relational database for structured business data (location, category, hours)
- A vector index for semantic matching across names, descriptions, and reviews
- An NLP pipeline to extract menu items and cuisine types from unstructured review text
- A knowledge graph linking food terms to cuisine categories
- A ranking model trained on user engagement signals

That's five systems. Google packages it as one API call.

## The Practical Takeaway

For developers building local search or restaurant discovery features: **don't reinvent this wheel.** The Google Places API at $32 per 1,000 requests (Text Search) is buying you access to a system that has been refined with billions of queries and petabytes of structured data. Your FTS5 index is not competing.

Where your own search infrastructure *does* make sense: when you have proprietary data Google doesn't (internal reviews, supply chain info, private ratings), or when you need search behavior Google won't give you (custom ranking, filtered facets, integration with your own recommendation engine).

For everything else, the search giant has earned its name.

## Addendum: Why No One Else Can Do This

It's worth pausing to ask: could a well-funded competitor replicate what Google's Text Search does here?

The short answer is no — not at this precision, and probably not for a long time.

**The unreplicable asset: behavioral data.** When millions of users search "うなぎ 浜松," click on a result, get directions, and physically visit the restaurant, Google captures that entire funnel. This implicit ground truth — "people who searched for eel actually went to *this* place" — is the ultimate ranking signal. No amount of engineering can substitute for two decades of global search-and-visit data. Even Apple, with effectively unlimited capital and its own Maps platform, has struggled to match Google's local search quality.

**The network effect of Business Profiles.** Over 200 million businesses worldwide have claimed their Google Business Profiles, voluntarily providing structured data about their cuisine, menus, and categories. This is free, first-party, continuously updated data from the businesses themselves. A competitor would need to convince millions of restaurant owners to register on a second platform — a cold-start problem that money alone doesn't solve.

**The graveyard of attempts.** Bing Maps, Yahoo! Local (Japan), Yelp's Japan expansion — all tried to build competitive local search. None came close to this level of precision for a query like "eel restaurants in Shizuoka." The common failure mode: without behavioral data to calibrate ranking, you either get too much noise (every restaurant that ever mentioned eel) or too little recall (only restaurants with "unagi" in the name).

**What *is* replicable.** The individual technologies — vector embeddings, knowledge graphs, structured data indexing — are all available as open-source components. You could stitch together OpenStreetMap + a review corpus + a multilingual embedding model and get something functional. It would work. It would also be an order of magnitude less precise, because the "last 5%" of search quality depends on signals that only a dominant consumer search engine can collect.

This is the real moat. Not the algorithm, but the data flywheel: more users → more behavioral signal → better ranking → more users. At $0.032 per request, the Google Places API is arguably underpriced for what it gives you — access to a system that no competitor can replicate from scratch, no matter how good their engineers are.

---

*I'm a semi-retired patent lawyer in Japan who started coding in December 2024. I build AI-powered search tools including [PatentLLM](https://patentllm.org) (3.5M US patent search engine) and various local-LLM applications on a single RTX 5090. This eel restaurant project is part of a broader exploration of what you can build by combining Google's APIs with local AI inference.*
