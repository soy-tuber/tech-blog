---
title: "Why Google Wasn't Indexing My FastAPI Site — The HEAD Request Trap"
date: 2026-03-16
topics: ["fastapi", "python", "seo", "webdev"]
published: true
canonical_url: "https://dev.to/soytuber/why-google-wasnt-indexing-my-fastapi-site-the-head-request-trap-1mjk"
devto_url: "https://dev.to/soytuber/why-google-wasnt-indexing-my-fastapi-site-the-head-request-trap-1mjk"
devto_id: 3360532
---

## The Symptom: 93 Pages Invisible to Google

I run a technical blog on FastAPI behind Cloudflare Tunnel. Google Search Console showed:

- **Server error (5xx)**: 1 page
- **Discovered — currently not indexed**: 93 pages

The site worked perfectly in a browser. Every page returned 200. Sitemap was valid. `robots.txt` allowed everything. So what was wrong?

## The Clue: HEAD Returns 405

```bash
curl -s -o /dev/null -w "%{http_code}" https://media.patentllm.org/
# 200 ✓

curl -s -o /dev/null -w "%{http_code}" -X HEAD https://media.patentllm.org/
# 405 ✗
```

Every page rejected HEAD requests with **405 Method Not Allowed**.

Googlebot uses HEAD requests during crawling to check pages before fetching full content. When HEAD returns 405, Google logs it as a server error and the page gets stuck in "Discovered — currently not indexed" limbo.

## Root Cause: FastAPI + Starlette Version

**FastAPI 0.133.1 with Starlette 0.52.1 does not automatically handle HEAD requests on GET routes.**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
def index():
    return {"hello": "world"}

client = TestClient(app)
print("GET:", client.get("/").status_code)    # 200
print("HEAD:", client.head("/").status_code)  # 405
```

This isn't a bug in your code. It's a framework behavior change — earlier Starlette versions handled HEAD implicitly.

## The Fix: One Middleware

```python
@app.middleware("http")
async def handle_head_requests(request: Request, call_next):
    if request.method == "HEAD":
        request.scope["method"] = "GET"
        response = await call_next(request)
        response.body = b""
        return response
    return await call_next(request)
```

After deploying:

```bash
curl -s -o /dev/null -w "%{http_code}" -X HEAD https://media.patentllm.org/
# 200 ✓
```

## Are You Affected?

```bash
curl -s -o /dev/null -w "HEAD: %{http_code}\n" -X HEAD https://your-site.com/
curl -s -o /dev/null -w "GET:  %{http_code}\n" https://your-site.com/
```

If HEAD returns 405 and GET returns 200, you have this problem.

## Takeaways

1. **Test with HEAD, not just GET.** Browsers and health checks only use GET.
2. **GSC errors are real.** When monitoring shows all-green but GSC reports errors, something about *how* Google accesses your site differs from how you test it.
3. **Framework defaults change between versions.** Don't assume HTTP method handling is stable across upgrades.
