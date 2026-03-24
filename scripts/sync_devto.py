"""Fetch all published articles from Dev.to and write as Jekyll _articles/*.md.

Read-only against Dev.to (GET only). Writes locally to _articles/.

Usage:
  python3 scripts/sync_devto.py              # Fetch & write all
  python3 scripts/sync_devto.py --dry-run    # Preview without writing
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

DEVTO_USERNAME = "soytuber"
ARTICLES_DIR = Path(__file__).resolve().parent.parent / "_articles"
PER_PAGE = 100
API_BASE = "https://dev.to/api"


def fetch_articles_list() -> list[dict]:
    """GET all published articles (paginated)."""
    all_articles = []
    page = 1
    while True:
        url = f"{API_BASE}/articles?username={DEVTO_USERNAME}&per_page={PER_PAGE}&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": "tech-blog-sync/1.0"})
        with urllib.request.urlopen(req) as resp:
            articles = json.loads(resp.read())
        if not articles:
            break
        all_articles.extend(articles)
        page += 1
        time.sleep(0.5)
    return all_articles


def fetch_article_detail(article_id: int) -> dict:
    """GET single article with body_markdown."""
    url = f"{API_BASE}/articles/{article_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "tech-blog-sync/1.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def slugify(title: str, article_id: int) -> str:
    """Create a filesystem-safe slug from title."""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    slug = slug[:80]
    return f"devto-{article_id}-{slug}"


def to_jekyll_md(article: dict) -> str:
    """Convert Dev.to article to Jekyll-compatible markdown with frontmatter."""
    title = article.get("title", "").replace('"', '\\"')
    canonical = article.get("canonical_url", "")
    tags = article.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    published_at = article.get("published_at", "")
    date_str = published_at[:10] if published_at else ""
    devto_url = article.get("url", "")
    body = article.get("body_markdown", "")

    frontmatter = f'''---
title: "{title}"
date: {date_str}
topics: {json.dumps(tags)}
published: true
canonical_url: "{canonical}"
devto_url: "{devto_url}"
devto_id: {article.get("id", 0)}
---'''

    return f"{frontmatter}\n\n{body}\n"


def main():
    dry_run = "--dry-run" in sys.argv
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching article list from Dev.to (@{DEVTO_USERNAME})...")
    articles = fetch_articles_list()
    print(f"Found {len(articles)} published articles.")

    written = 0
    for i, summary in enumerate(articles):
        article_id = summary["id"]
        title = summary.get("title", "")
        slug = slugify(title, article_id)
        filepath = ARTICLES_DIR / f"{slug}.md"

        print(f"  [{i+1}/{len(articles)}] {title[:60]}...", end=" ")

        if dry_run:
            print(f"-> {filepath.name} (dry-run)")
            continue

        detail = fetch_article_detail(article_id)
        md = to_jekyll_md(detail)
        filepath.write_text(md, encoding="utf-8")
        written += 1
        print(f"-> {filepath.name}")

        # Rate limit: Dev.to allows ~30 req/min for unauthenticated
        time.sleep(2)

    print(f"\nDone! Wrote {written} articles to {ARTICLES_DIR}")


if __name__ == "__main__":
    main()
