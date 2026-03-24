---
title: "Strategic Data Organization Techniques Using SQLite, JSONL, XML, and TSV: Lessons"
date: 2026-03-08
topics: ["devtools", "python", "productivity"]
published: true
canonical_url: "https://media.patentllm.org/en/blog/dev-tool/data-wrangling-practice"
devto_url: "https://dev.to/soytuber/strategic-data-organization-techniques-using-sqlite-jsonl-xml-and-tsv-lessons-57nh"
devto_id: 3326322
---

## Introduction

PatentLLM (patent search AI) and HanreiLLM (case law search AI) are both personal projects built with Python + Streamlit + SQLite. Through their development, I realized that the choice of data format directly impacts an application's maintainability and development speed. This article organizes the criteria for choosing between different data formats and the implementation know-how gained from actually using them.

## SQLite3: Application Backend

Both PatentLLM and HanreiLLM use SQLite3 for storing searchable data.

Reasons for Selection:
*   No server process required. Self-contained in a single .db file.
*   FTS5 (full-text search) is available out-of-the-box.
*   Python's `sqlite3` module is part of the standard library.
*   Good compatibility with Streamlit (read-heavy use cases).

In Hanrei-DB, case law texts are indexed with FTS5, combining keyword search with AI summarization by Gemini 3.1 Pro.

```bash
import sqlite3

conn = sqlite3.connect("hanrei.db")
conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS cases USING fts5(title, content)")

# 検索
results = conn.execute(
    "SELECT title, snippet(cases, 1, '<b>', '</b>', '...', 30) FROM cases WHERE cases MATCH ?",
    ("損害賠償 AND 契約解除",)
).fetchall()
```

Points to Note:
*   Weak against concurrent writes (single writer even in WAL mode).
*   Since Streamlit scripts are re-executed for each request, connections should be cached or managed within the request scope.
*   No issues up to several hundred thousand records. Beyond that, index design becomes crucial.

## JSONL: Data Exchange with LLMs

JSONL is the easiest format to handle when interacting with the Gemini API or local LLMs.

```bash
{"id": "H25-01234", "title": "損害賠償請求事件", "summary": "...", "label": "民事"}
{"id": "H26-05678", "title": "特許権侵害差止請求事件", "summary": "...", "label": "知財"}
```

Advantages:
*   One record per line allows for stream processing (no need to load everything into memory).
*   Easy to append (just append to the end of the file).
*   If one line is corrupted, it doesn't affect other lines.
*   Contents can be instantly checked with the `jq` command.

```bash
# 件数確認
wc -l cases.jsonl

# 先頭3件を整形表示
head -3 cases.jsonl | jq .

# 特定ラベルだけ抽出
cat cases.jsonl | jq -r 'select(.label == "知財") | .title'
```

In PatentLLM, I built a pipeline that converts CSV data from the Japan Patent Office into JSONL before loading it into SQLite. This CSV → JSONL → SQLite flow facilitates intermediate data validation.

## XML: Blog Post Management

This blog (Local AI Dev Log) itself manages article data in XML. It's configured so that FastAPI reads the XML on request and renders it with Jinja2 templates.

```bash
<articles>
  <item>
    <id>data-wrangling-practice</id>
    <category>data</category>
    <title>SQLite・JSONL・XML・TSVを使い分けるデータ整理術</title>
    <price>0</price>
    <summary>...</summary>
    <content>...</content>
  </item>
</articles>
```

Reasons for Choosing XML:
*   The number of articles is only a few dozen, not enough to warrant a database.
*   `ElementTree` is in the standard library, meaning zero external dependencies.
*   Can naturally express hierarchical structures like categories and tags.
*   Manual editing is possible (human-readable).

```bash
import xml.etree.ElementTree as ET

tree = ET.parse("data/articles_merged.xml")
root = tree.getroot()
for item in root.findall("item"):
    if item.find("category").text == "llm":
        print(item.find("title").text)
```

While it would be better to migrate to SQLite if the number exceeds several hundred, XML is sufficient for managing around 30-50 blog posts.

## TSV/CSV: Importing External Data

Data acquired externally, such as government data, financial data APIs, and scraping results, often comes in CSV or TSV format.

PatentLLM imports public data (CSV) from the Japan Patent Office.

```bash
import csv
import sqlite3
import json

conn = sqlite3.connect("patent.db")
conn.execute("CREATE TABLE IF NOT EXISTS patents (id TEXT PRIMARY KEY, title TEXT, abstract TEXT, date TEXT)")

with open("patents.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        conn.execute(
            "INSERT OR IGNORE INTO patents VALUES (?, ?, ?, ?)",
            (row["出願番号"], row["発明の名称"], row["要約"], row["出願日"])
        )
conn.commit()
```

CSV Pitfalls:
*   Encoding issues (Shift_JIS, UTF-8 with BOM).
*   Newlines and commas within fields (improper quoting).
*   Lack of type information (distinguishing numbers from strings is the responsibility of the reader).

As a countermeasure, inserting an intermediate step to convert to JSONL during import makes data validation easier.

```bash
# CSV → JSONL変換
import csv, json

with open("patents.csv", encoding="utf-8") as f_in, open("patents.jsonl", "w", encoding="utf-8") as f_out:
    for row in csv.DictReader(f_in):
        f_out.write(json.dumps(row, ensure_ascii=False) + "\n")
```

## Summary of Usage

*   Application backend (search, persistence) → SQLite3
*   Data transfer with LLMs, training data → JSONL
*   Management of a small number of structured content → XML
*   Entry point for external data import → CSV/TSV (as an intermediate step)

Common principle: Choose text-based formats whose contents can be easily inspected with tools like `cat` or `jq`. Binary formats (e.g., Parquet, Protocol Buffers) can wait for their turn until scenarios involving millions of records or where type safety is essential.
